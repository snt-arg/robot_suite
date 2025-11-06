# To handle ROS node
import rclpy

# ----- ROS messages
from std_msgs.msg import String, Bool


# person tracked messages and bounding boxes messages
from person_tracking_msgs.msg import AllBoundingBoxes, Box
from person_tracking_msgs.srv import TrackingMode


from plugin_base.plugin_base import PluginNode, NodeState

from collections import deque

from copy import copy

from typing import Optional, Any

import json

from math import pi

import py_trees

from person_tracking_helpers.helpers import (
    equal_box_msg,
    overlapping_area,
    calculate_midpoint_box,
    convert_landmarks_to_box,
    equal_allBoundingBoxes_msg,
)


###################################################################################################################################
class Tracker(PluginNode):

    # topic names
    pilot_topic = "/person_tracked"
    bounding_boxes_topic = "/all_bounding_boxes"
    llm_tracking_signal_topic = "/tracking_signal_llm"
    hand_tracking_signal_topic = "/tracking_signal_gesture"
    tracking_status_topic = "/tracking_status"

    # tracking mode is either llm or hand
    tracking_mode = "llm"  # or  "hand"

    # service on which to send requests to change the tracking mode
    tracking_mode_srv = "/tracking_mode_srv"

    # number of iteration the pilot's position is unchanged before concluding that the person is lost.
    max_no_update_before_lost = 30

    max_length_midpoint_queue = 2

    # subscribers
    sub_bounding_boxes = None
    sub_llm_tracking_signal = None
    sub_hand_tracking_signal = None

    # publishers
    publisher_pilot = None
    publisher_tracking_status = None

    # service
    service_tracking_mode = None

    overlapping_method = "intersection"

    target_class = "person"
    min_overlap = 0.09

    rotation_speed = pi / 7
    rotation_angle = pi / 7

    def __init__(self, name):

        # creating the Node
        super().__init__(name)

        # initializing parameters
        self._init_parameters()

        # initializing subscribers
        self._init_subscriptions()

        # initializing publishers
        self._init_publishers()

        # initializing services
        self._init_services()

        # variable to receive bounding boxes containing all persons detected
        self.boxes = None

        # coordinates of the current bounding box around the pilot person
        self.pilot_box = None

        # boolean variable to know whether to start or stop the tracking when receiving a tracking signal
        self.tracking = False

        # variable to count since how much iteration we didn't update the position of the person tracked.
        # If the position didn't change we can conclude that the person went out of the field of view of the camera, and we can rotate.
        self.no_update_count = None  # in nanoseconds

        self.last_received_bounding_boxes_time = None  # in nanoseconds

        # Queue to keep the last nonempty midpoints. Help to calculate the trajectory of the person before he got lost
        self.midpoint_queue = deque(maxlen=self.max_length_midpoint_queue)

        ### test
        # self.i = 0
        ### end test

    def _init_parameters(self) -> None:
        """Method to initialize parameters such as ROS topics' names"""

        self.declare_parameter("pilot_topic", self.pilot_topic)
        self.declare_parameter("bounding_boxes_topic", self.bounding_boxes_topic)
        self.declare_parameter(
            "llm_tracking_signal_topic", self.llm_tracking_signal_topic
        )
        self.declare_parameter(
            "hand_tracking_signal_topic", self.hand_tracking_signal_topic
        )
        self.declare_parameter("tracking_status_topic", self.tracking_status_topic)

        self.declare_parameter(
            "max_no_update_before_lost", self.max_no_update_before_lost
        )
        self.declare_parameter("overlapping_method", self.overlapping_method)

        self.declare_parameter("tracking_mode", self.tracking_mode)

        self.declare_parameter("tracking_mode_srv", self.tracking_mode_srv)

        self.pilot_topic = (
            self.get_parameter("pilot_topic").get_parameter_value().string_value
        )
        self.bounding_boxes_topic = (
            self.get_parameter("bounding_boxes_topic")
            .get_parameter_value()
            .string_value
        )

        self.llm_tracking_signal_topic = (
            self.get_parameter("llm_tracking_signal_topic")
            .get_parameter_value()
            .string_value
        )

        self.hand_tracking_signal_topic = (
            self.get_parameter("hand_tracking_signal_topic")
            .get_parameter_value()
            .string_value
        )

        self.tracking_status_topic = (
            self.get_parameter("tracking_status_topic")
            .get_parameter_value()
            .string_value
        )

        self.max_no_update_before_lost = (
            self.get_parameter("max_no_update_before_lost")
            .get_parameter_value()
            .integer_value
        )
        self.overlapping_method = (
            self.get_parameter("overlapping_method").get_parameter_value().string_value
        )
        self.tracking_mode = (
            self.get_parameter("tracking_mode").get_parameter_value().string_value
        )

        self.tracking_mode_srv = (
            self.get_parameter("tracking_mode_srv").get_parameter_value().string_value
        )

    def _init_publishers(self) -> None:
        """Method to initialize publishers"""
        self.publisher_pilot = self.create_publisher(Box, self.pilot_topic, 10)
        self.publisher_tracking_status = self.create_publisher(
            Bool, self.tracking_status_topic, 10
        )

    def _init_subscriptions(self) -> None:
        """Method to initialize subscriptions"""
        self.sub_bounding_boxes = self.create_subscription(
            AllBoundingBoxes,
            self.bounding_boxes_topic,
            self.bounding_boxes_listener_callback,
            5,
        )
        self.sub_llm_tracking_signal = self.create_subscription(
            String,
            self.llm_tracking_signal_topic,
            self.llm_tracking_signal_listener_callback,
            5,
        )
        self.sub_hand_tracking_signal = self.create_subscription(
            String,
            self.hand_tracking_signal_topic,
            self.hand_tracking_signal_listener_callback,
            5,
        )

    def _init_services(self) -> None:
        """Method to initialize services"""
        self.service_tracking_mode = self.create_service(
            TrackingMode, self.tracking_mode_srv, self.tracking_mode_service_callback
        )

    ########################### First Subscriber ##################################################################################################
    def bounding_boxes_listener_callback(self, boxes_msg):
        """Callback function for the subscriber node (to topic /all_bounding_boxes).
        For each bounding box received, save it in a variable for processing"""

        self.get_logger().debug("\nBounding boxes message received")
        if self.boxes != None and equal_allBoundingBoxes_msg(
            self.boxes, boxes_msg
        ):  # if the boxes are not updated
            self.get_logger().debug(f"\nBoxes not updated!\n")
        else:
            self.get_logger().debug(f"\n#Boxes updated!#\n")
            self.boxes = boxes_msg
            self.last_received_bounding_boxes_time = self.get_clock().now().nanoseconds

            if self.person_lost():
                if self.boxes.bounding_boxes != []:
                    self.pilot_box = self.boxes.bounding_boxes[0]
                    self.tracking = True
                    self.no_update_count = 0
                    self.get_logger().info(
                        f"\n#######################\nAfter loosing the target, we started tracking a new person\n#######################\n"
                    )
                else:
                    self.get_logger().debug(f"\nEmpty list of bounding boxes\n")

            ### test to track someone without the llm and the hand gesture plugin

            # if self.boxes is not None and self.boxes.bounding_boxes != []:
            #     if self.i == 0:
            #         self.tracking = True
            #         bounding_boxes = copy(self.boxes.bounding_boxes)

            #         self.pilot_box = copy(bounding_boxes[0])
            #         midpoint = calculate_midpoint_box(self.pilot_box)

            #         self.get_logger().info(
            #             f"\nTest found the pilot person indicated in the tracking signal. Midpoint : {midpoint}\n"
            #         )

            #         self.publisher_pilot.publish(self.pilot_box)

            #     self.i += 1

            ### end test

    ######################### Second subscriber ####################################################################################################
    def llm_tracking_signal_listener_callback(self, signal_msg):
        """Callback function to receive the signal message to start tracking a person at a specific location"""
        self.get_logger().info(
            f"\n!!!Tracking signal received from llm module {signal_msg}!!!\n"
        )

        if self.tracking_mode == "llm":

            # test to track someone without the llm
            # signal_msg.data = '{"action": "tracking", "id": 0, "info": {"bottom_right": [0.5055210590362549, 1.0], "top_left": [0.2135268896818161, 0.03876398876309395], "YOLO_id": 2, "objects": []}}'
            # end test

            infodict = json.loads(signal_msg.data)

            # if we aren't tracking and receive a tracking signal prompting to start the tracking:
            if self.tracking == False and infodict["action"] == "tracking":
                bottom_right = infodict["info"]["bottom_right"]
                top_left = infodict["info"]["top_left"]
                id = infodict["info"]["YOLO_id"]

                # Search the pilot person box in our list of bounding boxes
                self.find_pilot_llm(top_left, bottom_right, id)

            # if we receive a message to stop the tracking.
            elif infodict["action"] == "stop_tracking":
                self.tracking = False
                self.pilot_box = None
                self.get_logger().info(
                    f"\nLlm commanded to stop the tracking, so we stopped!\n"
                )
        else:
            self.get_logger().info(
                f"\n!!!Didn't process the tracking signal because we aren't on LLM mode\n"
            )

    def find_pilot_llm(self, top_left_coordinates, bottom_right_coordinates, id):
        """Method to find the pilot in the list of bounding boxes"""
        max_overlap_encountered = -1
        best_box = None

        potential_pilot = Box()
        potential_pilot.top_left.x = top_left_coordinates[0]
        potential_pilot.top_left.y = top_left_coordinates[1]
        potential_pilot.bottom_right.x = bottom_right_coordinates[0]
        potential_pilot.bottom_right.y = bottom_right_coordinates[1]

        # assign also class and ID

        if self.boxes is not None:

            # trying to find the box of the pilot based on ID first, then based on overlapping area if Id fails
            for box in self.boxes.bounding_boxes:
                if box.box_class == self.target_class:
                    overlap = overlapping_area(
                        potential_pilot, box, self.overlapping_method
                    )
                    if id != -1 and id == box.box_id:
                        self.tracking = True
                        self.pilot_box = copy(box)
                        self.midpoint_queue.append(self.pilot_box)
                        self.no_update_count = 0
                        self.get_logger().info(
                            f"\nBased on ID , Started tracking {self.pilot_box}\n"
                        )
                        return

                    elif (
                        overlap > max_overlap_encountered
                        and overlap >= self.min_overlap
                    ):
                        max_overlap_encountered = overlap
                        best_box = copy(box)

            if max_overlap_encountered == -1:
                self.get_logger().info(
                    f"\nDidn't find the pilot indicated via llm in the list of bounding boxes\n"
                )
            else:
                self.tracking = True
                self.pilot_box = copy(best_box)
                self.midpoint_queue.append(self.pilot_box)
                self.no_update_count = 0
                self.get_logger().info(
                    f"\Based on overlap, Started tracking {self.pilot_box}\n"
                )
        else:
            self.get_logger().debug(
                f"\nDidn't received the list of bounding boxes yet\n"
            )

    ######################### Third subscriber ####################################################################################################
    def hand_tracking_signal_listener_callback(self, signal_msg):
        """Callback function to receive the signal message to start tracking a person at a specific location"""
        self.get_logger().info(
            f"\n!!!Tracking signal received from hand gestures module {signal_msg}!!!\n"
        )

        if self.tracking_mode == "hand":

            infodict = json.loads(signal_msg.data)

            # if we aren't tracking and receive a tracking signal prompting to start the tracking:
            if self.tracking == False and infodict["action"] == "tracking":

                right_hand_coordinates = infodict["right_hand"]["normalized_landmarks"]
                left_hand_coordinates = infodict["left_hand"]["normalized_landmarks"]

                # Search the pilot person box in our list of bounding boxes
                self.find_pilot_hand(right_hand_coordinates, left_hand_coordinates)

            # if we receive a message to stop the tracking.
            elif infodict["action"] == "stop_tracking":
                self.tracking = False
                self.pilot_box = None
                self.get_logger().info(
                    f"\nPilot did gesture to stop the tracking, so we stopped!\n"
                )
        else:
            self.get_logger().info(
                f"\n!!!Didn't process the tracking signal because we aren't on hand gestures mode\n"
            )

    def find_pilot_hand(self, right_hand_coordinates, left_hand_coordinates):
        """Method to find the person who did a gesture from the list of bounding boxes"""
        max_overlap_encountered = -1
        best_box = None

        hands_box = convert_landmarks_to_box(
            left_hand_coordinates, right_hand_coordinates
        )

        if self.boxes is not None:

            for box in self.boxes.bounding_boxes:

                if box.box_class == "person":
                    overlap = overlapping_area(hands_box, box, self.overlapping_method)
                    self.get_logger().debug(f"hand_box={hands_box}")
                    self.get_logger().debug(f"box={box}")
                    self.get_logger().debug(f"overlap = {overlap}")
                    if overlap > max_overlap_encountered:
                        max_overlap_encountered = overlap
                        best_box = box

            if max_overlap_encountered == -1:
                self.get_logger().info(
                    f"\nDidn't find the pilot who did the gestures in the list of bounding boxes\n"
                )
            else:
                self.tracking = True
                self.pilot_box = best_box
                self.midpoint_queue.append(self.pilot_box)
                self.no_update_count = 0
                self.get_logger().info(f"\nStarted tracking\n")
        else:
            self.get_logger().debug(
                f"\nDidn't received the list of bounding boxes yet\n"
            )

    ######################### First Publisher #####################################################################################################
    def pilot_callback(self):
        """This function listens to the /hand/landmarks topic, and waits to spot the person who did the triggering move.
        In case a person did the trigger move, the midpoint of the bounding box around that person is published on a the topic named /person_tracked.
        The last node (track_person.py) will subscribe to /person_tracked and send commands to the drone to follow the tracked person.
        """
        if self.pilot_box is not None:
            if self.tracking:
                self.update_pilot_position()

                if not self.person_lost():
                    self.publisher_pilot.publish(self.pilot_box)
                else:
                    self.tracking = False
                    self.pilot_box = None
                    self.get_logger().info(
                        f"\n#####\n#####\nWe lost the pilot person !! Tracking stopped\n#####\n#####\n"
                    )

            else:
                self.get_logger().debug(
                    "Not tracking. We don't publish the position of the pilot"
                )
        else:
            self.get_logger().debug("Pilot box is None")

    def update_pilot_position(self):
        """Method to update the position of the pilot based on the previous position and the current list of bounding boxes"""
        max_overlap_encountered = -1
        best_box = None

        if self.boxes is not None:
            if self.pilot_box is not None:

                # trying to update the position of the pilot based on ID first, then based on overlapping area if Id fails
                for box in self.boxes.bounding_boxes:
                    overlap = overlapping_area(
                        self.pilot_box, box, self.overlapping_method
                    )
                    if (
                        self.pilot_box.box_id != -1
                        and box.box_id == self.pilot_box.box_id
                        and box.box_class == self.pilot_box.box_class
                    ):
                        self.pilot_box = box
                        self.no_update_count = 0
                        self.midpoint_queue.append(self.pilot_box)
                        self.get_logger().debug(
                            f"\nWith ID, updated pilot's position to {self.pilot_box}\n"
                        )
                        return

                    elif (
                        overlap > max_overlap_encountered
                        and box.box_class == self.pilot_box.box_class
                    ):
                        max_overlap_encountered = overlap
                        best_box = copy(box)

                if max_overlap_encountered == -1:
                    self.no_update_count += 1
                    self.get_logger().debug(
                        f"\nNo update. Didn't find the pilot in the list of bounding boxes. Maybe the person is lost\n"
                    )
                elif equal_box_msg(self.pilot_box, best_box):
                    self.no_update_count += 1
                    self.get_logger().debug(
                        f"\nNo update. the pilot's position didn't change\n"
                    )
                else:
                    self.pilot_box = best_box
                    self.no_update_count = 0
                    self.midpoint_queue.append(self.pilot_box)
                    self.get_logger().debug(
                        f"\nWith overlap, updated pilot's position to {self.pilot_box}\n"
                    )

        else:
            self.get_logger().debug(
                f"\nDidn't received the list of bounding boxes yet\n"
            )

    def person_lost(self):
        """Function to call when someone is lost.
        Returns true when the person is lost and False else."""
        if self.no_update_count is not None:
            if self.no_update_count >= self.max_no_update_before_lost:
                return True
            else:
                return False
        else:
            return False

    def direction_person_lost(self) -> str | None:
        """Function to determine whether the drone should rotate left, right, up or down to find the lost person"""
        if len(self.midpoint_queue) == self.max_length_midpoint_queue:
            point_1 = calculate_midpoint_box(
                self.midpoint_queue[1]
            )  # most recent midpoint
            point_2 = calculate_midpoint_box(
                self.midpoint_queue[0]
            )  # previous midpoint

            if point_1.x >= point_2.x:
                return "right"
            else:
                return "left"

        else:
            self.get_logger().error(
                f"\nNot enough midpoints received yet to predict the person's position\n"
            )

        return None

    ######################### Second Publisher #####################################################################################################
    def tracking_status_callback(self):
        """This method is to publish the tracking status for other nodes of the package"""
        # If we didn't update the bounding boxes recently, we stop the tracking, maybe the connexion is interrupted:
        if (
            self.last_received_bounding_boxes_time is not None
            and self.get_clock().now().nanoseconds
            - self.last_received_bounding_boxes_time
            > 5e9
        ):
            self.tracking = False
            self.pilot_box = None

        msg = Bool()
        msg.data = self.tracking
        self.publisher_tracking_status.publish(msg)

    ######################### Service callback #####################################################################################################
    def tracking_mode_service_callback(self, request, response):
        """Callback function for the service to change the tracking mode"""
        if request.tracking_mode in ["llm", "hand"]:
            self.tracking_mode = request.tracking_mode

            self.tracking = False
            self.pilot_box = None

            self.get_logger().info(
                f"Tracking stopped to change mode",
                f"\nTracking mode changed to {self.tracking_mode} via service\n",
            )
            response.status = True
        else:
            self.get_logger().warning(
                f"\nTracking mode {request.tracking_mode} is not a valid tracking mode. It should be either 'llm' or 'hand'\n",
                f"Tracking continues and tracking mode unchanged : {self.tracking_mode}\n",
            )
            response.status = False

        return response

    ####################### Tick method ###########################################################################################################
    def tick(self, blackboard: Optional[dict["str", Any]] = None) -> NodeState:
        """This method is a mandatory for PluginBase node. It defines what we want our node to do.
        It gets called 20 times a second if state=RUNNING
        Here we call callback functions to publish a detection frame and the list of bounding boxes.
        """
        self.pilot_callback()
        self.tracking_status_callback()

        # Updating the blackboard with the current tracking mode for consistency with the Behaviour tree.
        try:
            if blackboard is not None:
                blackboard_tracking_mode = blackboard.get("tracking_mode")

                if self.tracking_mode != blackboard_tracking_mode:
                    blackboard["tracking_mode"] = self.tracking_mode

        except Exception as e:
            self.get_logger().error(f"Error updating blackboard tracking mode: {e}")

        # Rotating when the person is lost
        if self.person_lost():
            self.get_logger().debug("Pilot person lost")

            rotation_direction = self.direction_person_lost()

            if rotation_direction is not None and blackboard is not None:
                if blackboard.get("rotate_robot") is not None:
                    current_angle = (
                        blackboard["rotate_robot"]["total_rotated_angle"]
                        + self.rotation_angle
                    )
                else:
                    current_angle = 0
                blackboard["rotate_robot"] = {
                    "rotation_direction": rotation_direction,
                    "rotation_angle": self.rotation_angle,
                    "rotation_speed": self.rotation_speed,
                    "total_rotated_angle": current_angle,
                }

            return NodeState.FAILURE
        else:

            return NodeState.SUCCESS


#############################################################################################################################################################


def main(args=None):
    # Initialization ROS communication
    rclpy.init(args=args)

    # Node instantiation
    tracker = Tracker("tracker_node")

    # uncomment to see debug logs
    tracker.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)

    # Execute the callback function until the global executor is shutdown
    rclpy.spin(tracker)

    # destroy the node. It is not mandatory, since the garbage collection can do it
    tracker.destroy_node()

    rclpy.shutdown()
