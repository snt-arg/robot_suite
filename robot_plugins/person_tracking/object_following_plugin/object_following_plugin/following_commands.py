# for handling ROS node
import rclpy

# ROS Messages
import rclpy.logging
from std_msgs.msg import Bool

# ROS Twist message import. This message type is used to send commands to the drone.
from geometry_msgs.msg import Twist

# custom message containing  the bounding box surrounding the tracked person
from person_tracking_msgs.msg import Box, AllBoundingBoxes

from object_following_plugin.pid import P
from object_following_plugin.mpc import MPC

from typing import Optional, Any

from threading import Thread

from math import pi


from plugin_base.plugin_base import PluginNode, NodeState
from person_tracking_helpers.helpers import (
    calculate_box_size,
    calculate_midpoint_box,
    extract_point_msg,
)


##NB : all directions : left, right... are from the drone's perspective


class FollowingCommands(PluginNode):

    person_tracked_topic = "/person_tracked"  # carries the position of the tracked person (midpoint and box)
    commands_topic = "/cmd_vel"  # carries Twist msgs
    tracking_status_topic = "/tracking_status"
    all_bounding_boxes_topic = "/all_bounding_boxes"  # carries AllBoundingBoxes msgs

    # subscribers
    sub_person_tracked = None

    sub_tracking_status = None

    sub_all_bounding_boxes = None

    # publishers
    publisher_commands = None

    # control method for autonomous tracking. There are three methods available : "on/off", "P" and "MPC"
    control_method = "P"  # "on/off", "P" or "MPC" . Note: P is for P controller

    # on-off parameters
    lower_threshold_midpoint_to_rotate = None
    higher_threshold_midpoint_to_rotate = None
    lower_threshold_midpoint = None
    higher_threshold_midpoint = None

    lower_threshold_box_size = None
    higher_threshold_box_size = None

    # PID parameters
    pid_y_axis = None  # Controller for y axis (horizontal position to keep the person within the field of view)
    pid_x_axis = None
    pid_z_axis = None

    # MDP parameters
    mpc_y_axis = None
    mpc_x_axis = None

    # rotation values
    angular_speed = pi / 10
    target_angle = pi / 15

    def __init__(self, name):
        # Creating the Node
        super().__init__(name)

        # init topic names
        self._init_parameters()

        # init subscribers
        self._init_subscriptions()

        # init publishers
        self._init_publishers()

        # init control method parameters
        self._init_control()

        self.person_tracked_midpoint = None

        self.bounding_box_size = None

        self.pilot_id = None

        self.commands_msg = None

        self.tracking = False

        # if True, then we avoid collision. If False, we just publish the following comands with no modification.
        self.avoid_collision = False  # boolean variable to decide whether we should avoid collision or just send the commands messages.

        self.boxes = None

    def _init_parameters(self) -> None:
        """Method to initialize parameters such as ROS topics' names"""

        # Topic names

        self.declare_parameter("person_tracked_topic", self.person_tracked_topic)
        self.declare_parameter("commands_topic", self.commands_topic)
        self.declare_parameter("tracking_status_topic", self.tracking_status_topic)
        self.declare_parameter(
            "all_bounding_boxes_topic", self.all_bounding_boxes_topic
        )

        self.declare_parameter("control_method", self.control_method)

        self.person_tracked_topic = (
            self.get_parameter("person_tracked_topic")
            .get_parameter_value()
            .string_value
        )
        self.commands_topic = (
            self.get_parameter("commands_topic").get_parameter_value().string_value
        )

        self.tracking_status_topic = (
            self.get_parameter("tracking_status_topic")
            .get_parameter_value()
            .string_value
        )

        self.control_method = (
            self.get_parameter("control_method").get_parameter_value().string_value
        )

        self.all_bounding_boxes_topic = (
            self.get_parameter("all_bounding_boxes_topic")
            .get_parameter_value()
            .string_value
        )

    def _init_publishers(self) -> None:
        """Method to initialize publishers"""

        # publishers
        self.publisher_commands = self.create_publisher(Twist, self.commands_topic, 10)

    def _init_subscriptions(self) -> None:
        """Method to initialize subscriptions"""
        self.sub_person_tracked = self.create_subscription(
            Box, self.person_tracked_topic, self.person_tracked_callback, 5
        )

        self.sub_tracking_status = self.create_subscription(
            Bool, self.tracking_status_topic, self.tracking_status_callback, 5
        )

        self.sub_all_bounding_boxes = self.create_subscription(
            AllBoundingBoxes,
            self.all_bounding_boxes_topic,
            self.all_bounding_boxes_callback,
            5,
        )

    def _init_control(self) -> None:
        """Method to initialize the control parameters, depending on the control method"""
        self.lower_threshold_midpoint_to_rotate = 0.1
        self.higher_threshold_midpoint_to_rotate = 0.7

        if self.control_method.lower() == "on/off":

            # self.threshold_midpoint = 0.5
            self.lower_threshold_midpoint = 0.3
            self.higher_threshold_midpoint = 0.7

            self.lower_threshold_box_size = 0.85
            self.higher_threshold_box_size = 1

        elif self.control_method.lower() == "p":
            # Controller for y axis (horizontal position to keep the person within the field of view)

            self.pid_y_axis = P(0.5, 1.5, (-0.15, 0.15))

            # Controller for bounding box size (distance between the drone and the person)
            self.pid_x_axis = P(0.8, 1, (-0.25, 0.25))

        elif self.control_method.lower() == "mpc":
            self.mpc_x_axis = MPC(10, 0.5, 0.5)
            self.mpc_y_axis = MPC(10, 1.25, 1.25)

        else:
            raise ValueError("Unknown control method")

    ###########################first subscriber###########################################################################################
    def person_tracked_callback(self, msg):
        """Callback function for the subscriber node (to topic /person_tracked).
        Receives the midpoint of the bounding box surrounding the person tracked"""
        self.get_logger().debug("Pilot's position received")
        self.person_tracked_midpoint = calculate_midpoint_box(msg)
        self.bounding_box_size = calculate_box_size(msg)
        self.pilot_id = msg.box_id
        self.get_logger().debug(
            f"Person tracked midpoint: {self.person_tracked_midpoint}"
        )
        self.get_logger().debug(f"Bounding box size: {self.bounding_box_size}")
        self.get_logger().debug(f"Pilot id: {self.pilot_id}")

    ###########################second subscriber###########################################################################################

    def all_bounding_boxes_callback(self, boxes_msg):
        """Callback function for the subscriber node (to topic /all_bounding_boxes).
        Receives the list of all bounding boxes surrounding all detected persons and objects
        """
        self.get_logger().debug("All bounding boxes received")
        self.boxes = boxes_msg

    ######################### Publisher #####################################################################################################
    def commands_callback(self):
        """This function makes appropriate commands messages in order to keep the tracked person within the camera's field while ensuring safety"""
        self.commands_msg = Twist()
        self.commands_msg.linear.x = 0.0
        self.commands_msg.linear.y = 0.0
        self.commands_msg.linear.z = 0.0
        self.commands_msg.angular.x = 0.0
        self.commands_msg.angular.y = 0.0
        self.commands_msg.angular.z = 0.0

        if (self.person_tracked_midpoint is not None) and (
            self.bounding_box_size is not None
        ):

            following_commands = self.control_commands()

            if self.avoid_collision:
                self.commands_msg = self.compute_anti_collision_vector(
                    following_commands
                )
            else:
                self.commands_msg = following_commands

            self.publisher_commands.publish(self.commands_msg)

            # rotation
            if self.person_tracked_midpoint.x < self.lower_threshold_midpoint_to_rotate:
                self.get_logger().debug("rotate left")
                rotationThread = Thread(
                    target=self.rotation,
                    args=(self.angular_speed, self.target_angle),
                    daemon=True,
                )
                rotationThread.start()

            elif (
                self.person_tracked_midpoint.x
                > self.higher_threshold_midpoint_to_rotate
            ):
                self.get_logger().debug("rotate right")
                rotationThread = Thread(
                    target=self.rotation,
                    args=(-self.angular_speed, -self.target_angle),
                    daemon=True,
                )
                rotationThread.start()

    def control_commands(self) -> Twist:
        """Function to determine the command to send to the drone given the current position of the person
        in the camera's field, the distance between the person and the drone, and the control method
        """
        commands = Twist()
        if self.control_method.lower() == "on/off":

            # horizontal move
            if (
                self.person_tracked_midpoint.x
                >= self.lower_threshold_midpoint_to_rotate
                and self.person_tracked_midpoint.x <= self.lower_threshold_midpoint
            ):
                self.get_logger().debug(
                    "move left"
                )  # (a in keyboard mode control station)
                commands.linear.y += 0.25

            elif (
                self.person_tracked_midpoint.x
                <= self.higher_threshold_midpoint_to_rotate
                and self.person_tracked_midpoint.x >= self.higher_threshold_midpoint
            ):
                self.get_logger().debug(
                    "move right"
                )  # (d in keyboard mode control station )
                commands.linear.y += -0.25

            # distance
            if self.bounding_box_size < self.lower_threshold_box_size:
                self.get_logger().debug("approach")
                commands.linear.x += 0.35

            elif self.bounding_box_size > self.higher_threshold_box_size:
                self.get_logger().debug("move back")
                commands.linear.x += -0.35

        elif self.control_method.lower() == "p":

            # horizontal move
            correction_y = self.pid_y_axis.compute(self.person_tracked_midpoint.x)
            commands.linear.y = correction_y

            # distance
            correction_x = self.pid_x_axis.compute(self.bounding_box_size)
            commands.linear.x = correction_x

        elif self.control_method.lower() == "mpc":
            # horizontal
            correction_y = self.mpc_y_axis.solve_mpc(self.person_tracked_midpoint.x)
            commands.linear.y = correction_y

            if correction_y > 0:
                self.get_logger().debug(
                    "move left"
                )  # (a in keyboard mode control station)
                commands.linear.y += 0.2

            elif correction_y < 0:
                self.get_logger().debug(
                    "move right"
                )  # (d in keyboard mode control station )
                commands.linear.y += -0.2

            # distance
            correction_x = self.mpc_x_axis.solve_mpc(self.bounding_box_size)
            commands.linear.x = correction_x

            if correction_x > 0:
                self.get_logger().debug("approach")
                commands.linear.x += 0.2
            elif correction_x < 0:
                self.get_logger().debug("move back")
                commands.linear.x += -0.2

        else:
            raise ValueError("Unknown control method")

        return commands

    def tracking_status_callback(self, msg):
        """Method to receive the tracking status"""
        self.tracking = msg.data
        self.get_logger().debug(f"Tracking status : {self.tracking}")

    def rotation(self, angular_speed, target_angle) -> None:
        """Function to send rotation commands to the drone.
        Returns True if the drone did a complete rotation (no one was found) and False else
        """
        rotation_commands_msg = Twist()

        current_angle = 0
        rotation_commands_msg.angular.z = angular_speed

        self.get_logger().info(
            f"Before rotating,  angular.z is {rotation_commands_msg.angular.z} and current_angle is {current_angle}"
        )

        t0 = self.get_clock().now()

        while abs(current_angle) <= abs(target_angle):

            self.publisher_commands.publish(rotation_commands_msg)
            t1 = self.get_clock().now()

            current_angle = rotation_commands_msg.angular.z * ((t1 - t0).to_msg().sec)

        self.get_logger().info(
            f"After rotating ,angular.z is {rotation_commands_msg.angular.z} and current_angle is {current_angle}"
        )

    def compute_anti_collision_vector(self, following_commands: Twist):
        """Function to compute the drone's vector based on the pilot's position and the following commands and the obstacles"""
        self.get_logger().debug("Computing drone vector")
        vectors = []
        sum_vectors_x = None
        image_center = 0.5  # because all coordinates are normalized in scale [1,1]
        final_vector = None

        if self.pilot_id is not None and self.boxes is not None:
            for box in self.boxes.bounding_boxes:
                if box.box_id != self.pilot_id:
                    obstacle_midpoint_x, _ = extract_point_msg(
                        calculate_midpoint_box(box)
                    )
                    obstacle_force = calculate_box_size(box)
                    obstacle_vector_x = (
                        image_center - obstacle_midpoint_x
                    ) * obstacle_force

                    vectors.append(obstacle_vector_x)

            self.get_logger().info(f"Vector forces : {vectors}")

            sum_vectors_x = sum(vectors) + following_commands.linear.y
            self.get_logger().info(f"Final sum : {sum_vectors_x}")

            final_vector = following_commands
            final_vector.linear.y = sum_vectors_x

        if self.pilot_id is None:
            self.get_logger().debug("Pilot Box ID not avalaible")
        if self.boxes is None:
            self.get_logger().debug("No boxes received")

        return final_vector

    ###################################################################################################################################
    def tick(self, blackboard: Optional[dict["str", Any]] = None) -> NodeState:
        """This method is a mandatory for PluginBase node. It defines what we want our node to do.
        It gets called 20 times a second if state=RUNNING
        Here we call callback functions to publish a detection frame and the list of bounding boxes.
        """
        if self.tracking:
            self.get_logger().debug("Tracking")
            self.commands_callback()
        return NodeState.SUCCESS


def main(args=None):
    # Intialization ROS communication
    rclpy.init(args=args)
    followingCommands = FollowingCommands("following_commands_node")

    # followingCommands.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)

    # execute the callback function until the global executor is shutdown
    rclpy.spin(followingCommands)

    # destroy the node. It is not mandatory, since the garbage collection can do it
    followingCommands.destroy_node()

    rclpy.shutdown()
