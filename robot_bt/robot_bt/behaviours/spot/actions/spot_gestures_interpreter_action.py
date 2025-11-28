from robot_bt.behaviours.shared.actions import Action
from typing import Optional
import time
import rclpy

import py_trees
from rclpy.node import Node
from std_srvs.srv import Trigger
from geometry_msgs.msg import Twist
from hand_gestures_msgs.msg import Landmarks

# from spot_msgs.action import RobotCommand
# from .simple_spot_commander import SimpleSpotCommander


# https://github.com/snt-arg/spot_ws/blob/update/packages/spot_sign_interpreter/spot_sign_interpreter/spot_sign_interpreter_node.py


class SpotGesturesInterpreterAction(Action):

    landmarks_topic: str = "/hand/landmarks"

    def __init__(
        self,
        robot_name: Optional[str] = None,
        node: Optional[Node] = None,
        filter_mode: bool = False,
    ) -> None:
        super().__init__(name="SpotGesturesInterpreterAction", bt_node=node)
        if self.node is None:
            raise ValueError("no ROS 2 node available.")

        self.landmarks_topic = (
            "/hand/landmarks" if filter_mode == False else "/hand/landmarks_from_pilot"
        )

        self.node.create_subscription(
            Landmarks, self.landmarks_topic, self.landmarks_callback, 10
        )

        self.stand_client = self.node.create_client(Trigger, "/byte/stand")
        self.sit_client = self.node.create_client(Trigger, "/byte/sit")
        self.cmd_vel_pub = self.node.create_publisher(Twist, "/byte/cmd_vel", 10)
        self.timer = self.node.create_timer(1 / 20, self.timer_callback)

        self.last_landmark_recv = None

        self.cmd_vel = Twist()
        self.is_sitted = False

    def landmarks_callback(self, msg: Landmarks):
        self.last_landmark_recv = msg

    def process_gestures(self, right_gesture: str, left_gesture: str):
        if right_gesture == "None" or left_gesture == "None":
            self.stop_spot()
        # Forward/backward
        if left_gesture == "Open_Palm":
            if right_gesture == "Pointing_Up":
                self.move_forward()
            elif right_gesture == "Victory":
                self.move_backward()

        # Left/right
        if left_gesture == "Pointing_Up" and right_gesture == "Closed_Fist":
            self.move_right()
        elif left_gesture == "Closed_Fist" and right_gesture == "Pointing_Up":
            self.move_left()

        # Rotation left/right
        if left_gesture == "Thumb_Up" and right_gesture == "Closed_Fist":
            self.rotate_right()
        elif left_gesture == "Closed_Fist" and right_gesture == "Thumb_Up":
            self.rotate_left()

        # Stand Up/Sit Down
        if left_gesture == "Open_Palm" and right_gesture == "Thumb_Up":
            self.stand_up()
        elif left_gesture == "Open_Palm" and right_gesture == "Thumb_Down":
            self.sit_down()

    def timer_callback(self):
        if not self.is_sitted:
            self.cmd_vel_pub.publish(self.cmd_vel)

    def move_forward(self):
        self.node.get_logger().info("Moving forward")
        self.cmd_vel.linear.x = 0.4

    def move_backward(self):
        self.node.get_logger().info("Moving backward")
        self.cmd_vel.linear.x = -0.4

    def move_left(self):
        self.node.get_logger().info("Moving left")
        self.cmd_vel.linear.y = 0.4

    def move_right(self):
        self.node.get_logger().info("Moving right")
        self.cmd_vel.linear.y = -0.4

    def rotate_left(self):
        self.node.get_logger().info("Rotating left")
        self.cmd_vel.angular.z = 1.0

    def rotate_right(self):
        self.node.get_logger().info("Rotating right")
        self.cmd_vel.angular.z = -1.0

    def stand_up(self):
        self.node.get_logger().info("Standing up")
        self.is_sitted = False
        self.stand_client.call_async(Trigger.Request())
        time.sleep(2)

    def sit_down(self):
        self.node.get_logger().info("Sitting down")
        self.is_sitted = True
        self.sit_client.call_async(Trigger.Request())
        time.sleep(2)

    def stop_spot(self):
        self.node.get_logger().info("Stopping")
        self.cmd_vel.linear.x = 0.0
        self.cmd_vel.linear.y = 0.0
        self.cmd_vel.angular.z = 0.0

    def update(self) -> py_trees.common.Status:

        if self.last_landmark_recv is None:
            return py_trees.common.Status.FAILURE

        msg = self.last_landmark_recv

        num_hands = 0
        if msg.right_hand.handedness != "":
            num_hands += 1
        if msg.left_hand.handedness != "":
            num_hands += 1

        if num_hands == 2:
            self.process_gestures(msg.right_hand.gesture, msg.left_hand.gesture)
        else:
            self.stop_spot()

        return py_trees.common.Status.SUCCESS
