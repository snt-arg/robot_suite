# for handling ROS node
import rclpy


# ROS Twist message import. This message type is used to send commands to the drone.
from geometry_msgs.msg import Twist

from std_msgs.msg import Bool

# custom message containing  the bounding box surrounding the tracked person
from person_tracking_msgs.msg import Box, AllBoundingBoxes


from plugin_base.plugin_base import PluginNode, NodeState
from person_tracking_helpers.helpers import (
    calculate_box_size,
    calculate_midpoint_box,
    extract_point_msg,
)

from copy import copy
from typing import Optional, Any

##NB : all directions : left, right... are from the drone's perspective


class CollisionAvoiding(PluginNode):

    person_tracked_topic = "/person_tracked"  # carries the position of the tracked person (midpoint and box)
    following_commands_topic = "/following_vel"  # carries Twist msgs
    commands_topic = "/cmd_vel"  # carries Twist msgs
    all_bounding_boxes_topic = "/all_bounding_boxes"  # carries AllBoundingBoxes msgs
    tracking_status_topic = "/tracking_status"  # carries Bool msgs

    # subscribers
    sub_person_tracked = None
    sub_following_commands = None
    sub_all_bounding_boxes = None
    sub_tracking_status = None

    # publishers
    publisher_commands = None

    def __init__(self, name):
        # Creating the Node
        super().__init__(name)

        # init topic names
        self._init_parameters()

        # init subscribers
        self._init_subscriptions()

        # init publishers
        self._init_publishers()

        self.drone_vector = None

        self.pilot_person = None

        self.commands_msg = None

        self.following_commands = None

        self.boxes = None

        self.tracking = False

        # if True, then we avoid collision. If False, we just publish the following comands with no modification.
        self.avoid_collision = False  # boolean variable to decide whether we should avoid collision or just send the commands messages.

    def _init_parameters(self) -> None:
        """Method to initialize parameters such as ROS topics' names"""

        # Topic names

        self.declare_parameter("person_tracked_topic", self.person_tracked_topic)
        self.declare_parameter(
            "following_commands_topic", self.following_commands_topic
        )
        self.declare_parameter(
            "all_bounding_boxes_topic", self.all_bounding_boxes_topic
        )
        self.declare_parameter("commands_topic", self.commands_topic)
        self.declare_parameter("tracking_status_topic", self.tracking_status_topic)

        self.person_tracked_topic = (
            self.get_parameter("person_tracked_topic")
            .get_parameter_value()
            .string_value
        )
        self.following_commands_topic = (
            self.get_parameter("following_commands_topic")
            .get_parameter_value()
            .string_value
        )
        self.all_bounding_boxes_topic = (
            self.get_parameter("all_bounding_boxes_topic")
            .get_parameter_value()
            .string_value
        )
        self.tracking_status_topic = (
            self.get_parameter("tracking_status_topic")
            .get_parameter_value()
            .string_value
        )
        self.commands_topic = (
            self.get_parameter("commands_topic").get_parameter_value().string_value
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
        self.sub_following_commands = self.create_subscription(
            Twist, self.following_commands_topic, self.following_commands_callback, 5
        )

    ###########################first subscriber###########################################################################################
    def person_tracked_callback(self, msg):
        """Callback function for the subscriber node (to topic /person_tracked).
        Receives the bounding box surrounding the person tracked"""
        self.get_logger().info("Pilot's position received")
        self.pilot_person = msg

    def tracking_status_callback(self, msg):
        """Callback function for the subscriber node (to topic /tracking_status).
        Receives the tracking status of the system"""
        self.tracking = msg.data

    def all_bounding_boxes_callback(self, boxes_msg):
        """Callback function for the subscriber node (to topic /all_bounding_boxes).
        Receives the list of all bounding boxes surrounding all detected persons and objects
        """
        self.get_logger().debug("All bounding boxes received")
        self.boxes = boxes_msg

    def following_commands_callback(self, msg):
        """Callback function for the subscriber node (to topic /following_commands).
        Receives the commands to follow the tracked person"""
        self.get_logger().debug("Following commands received")
        self.following_commands = msg

    ######################### Publisher #####################################################################################################
    def commands_callback(self):
        """"""
        self.commands_msg = Twist()

        if self.avoid_collision:
            self.commands_msg = self.compute_drone_vector()

        else:
            self.commands_msg = copy(self.following_commands)

        if self.commands_msg is not None:
            self.publisher_commands.publish(self.commands_msg)
            self.get_logger().info(
                f"Publishing commands on {self.commands_topic} : {self.commands_msg}"
            )
        self.get_logger().info(
            f"\nCollision commands: {self.commands_msg}\n following:{self.following_commands}"
        )

    def compute_drone_vector(self):
        """Function to compute the drone's vector based on the pilot's position and the following commands and the obstacles"""
        self.get_logger().debug("Computing drone vector")
        vectors = []
        sum_vectors_x = None
        image_center = 0.5  # because all coordinates are normalized in scale [1,1]
        final_vector = None

        if self.tracking:

            if (
                self.pilot_person is not None
                and self.boxes is not None
                and self.following_commands is not None
            ):
                for box in self.boxes.bounding_boxes:
                    if box.box_id != self.pilot_person.box_id:
                        obstacle_midpoint_x, _ = extract_point_msg(
                            calculate_midpoint_box(box)
                        )
                        obstacle_force = calculate_box_size(box)
                        obstacle_vector_x = (
                            image_center - obstacle_midpoint_x
                        ) * obstacle_force

                        vectors.append(obstacle_vector_x)

                self.get_logger().info(f"Vector forces : {vectors}")

                sum_vectors_x = sum(vectors) + self.following_commands.linear.y
                self.get_logger().info(f"Final sum : {sum_vectors_x}")

                final_vector = self.following_commands
                final_vector.linear.y = sum_vectors_x

            if self.pilot_person is None:
                self.get_logger().info("No pilot detected")
            if self.following_commands is None:
                self.get_logger().info("No following commands received")
            if self.boxes is None:
                self.get_logger().info("No boxes received")

        else:
            if self.boxes is not None:
                for box in self.boxes.bounding_boxes:

                    obstacle_midpoint_x, _ = extract_point_msg(
                        calculate_midpoint_box(box)
                    )
                    obstacle_force = calculate_box_size(box)
                    obstacle_vector_x = (
                        image_center - obstacle_midpoint_x
                    ) * obstacle_force

                    vectors.append(obstacle_vector_x)

                self.get_logger().info(f"Vector forces : {vectors}")
                sum_vectors_x = sum(vectors)
                self.get_logger().info(f"Final sum : {sum_vectors_x}")

                final_vector = Twist()
                final_vector.linear.y = sum_vectors_x
            else:
                self.get_logger().info("No boxes received. Final vector is None")

        return final_vector

    ###################################################################################################################################
    def tick(self, blackboard: Optional[dict["str", Any]] = None):
        """This method is a mandatory for PluginBase node. It defines what we want our node to do.
        It gets called 20 times a second if state=RUNNING
        Here we call callback functions to publish a detection frame and the list of bounding boxes.
        """
        print("Ticked\nTicked\nTicked.....\n")

        self.commands_callback()

        return NodeState.SUCCESS


def main(args=None):
    # Intialization ROS communication
    rclpy.init(args=args)
    collision_avoiding = CollisionAvoiding("collision_avoidance_node")

    # execute the callback function until the global executor is shutdown
    rclpy.spin(collision_avoiding)

    # destroy the node. It is not mandatory, since the garbage collection can do it
    collision_avoiding.destroy_node()

    rclpy.shutdown()
