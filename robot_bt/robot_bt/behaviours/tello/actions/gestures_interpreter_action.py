from typing import Optional
import random
from rclpy.node import Publisher, Subscription
from robot_bt.behaviours.shared.actions import Action
from std_msgs.msg import Empty
from geometry_msgs.msg import Twist
import py_trees
from hand_gestures_msgs.msg import Landmarks
from tello_msgs.msg import FlipControl


class GesturesInterpreterAction(Action):
    land_topic: str = "/land"
    land_pub: Publisher
    takeoff_topic: str = "/takeoff"
    takeoff_pub: Publisher
    flip_topic: str = "/flip"
    flip_pub: Publisher
    cmd_topic: str = "/cmd_vel"
    cmd_pub: Publisher
    landmarks_topic: str = "/hand/landmarks"
    landmakrs_sub: Subscription
    last_landmark_recv: Optional[Landmarks] = None

    max_lin_speed: float = 0.3
    max_ang_speed: float = 1.0

    def __init__(self, name, bt_node, filter_mode):
        super().__init__(name, bt_node)
        self.landmarks_topic = (
            "/hand/landmarks" if filter_mode == False else "/hand/landmarks_from_pilot"
        )

    def setup(self) -> None:  # type: ignore
        self.land_pub = self.node.create_publisher(Empty, self.land_topic, 1)
        self.takeoff_pub = self.node.create_publisher(Empty, self.takeoff_topic, 1)
        self.flip_pub = self.node.create_publisher(FlipControl, self.flip_topic, 1)
        self.cmd_pub = self.node.create_publisher(Twist, self.cmd_topic, 10)
        self.landmarks_sub = self.node.create_subscription(
            Landmarks, self.landmarks_topic, self.landmarks_callback, 10
        )

    def landmarks_callback(self, msg: Landmarks) -> None:
        self.last_landmark_recv = msg

    def nbr_hands_detected(self, msg: Landmarks) -> int:
        return int(msg.right_hand.handedness != "") + int(
            msg.left_hand.handedness != ""
        )

    def can_takeoff(self, msg: Landmarks) -> bool:
        if self.nbr_hands_detected(msg) != 1:
            return False

        if not msg.right_hand.gesture == "ILoveYou":
            return False

        return True

    def can_land(self, msg: Landmarks) -> bool:
        if self.nbr_hands_detected(msg) != 2:
            return False

        if not (
            msg.left_hand.gesture == "Open_Palm"
            and msg.right_hand.gesture == "Thumb_Down"
        ):
            return False

        return True

    def can_flip(self, msg: Landmarks) -> bool:
        if self.nbr_hands_detected(msg) != 2:
            return False

        if not (
            msg.left_hand.gesture == "ILoveYou" and msg.right_hand.gesture == "ILoveYou"
        ):
            return False

        return True

    def build_move(self, msg: Landmarks) -> Twist | None:
        if self.nbr_hands_detected(msg) != 2:
            return None

        left_gesture, right_gesture = msg.left_hand.gesture, msg.right_hand.gesture

        cmd_vel = Twist()

        # Forward/backward
        if left_gesture == "Open_Palm":
            if right_gesture == "Pointing_Up":
                cmd_vel.linear.x = self.max_lin_speed
            elif right_gesture == "Victory":
                cmd_vel.linear.x = -self.max_lin_speed

        # Left/right
        if left_gesture == "Pointing_Up" and right_gesture == "Closed_Fist":
            cmd_vel.linear.y = -self.max_lin_speed
        elif left_gesture == "Closed_Fist" and right_gesture == "Pointing_Up":
            cmd_vel.linear.y = self.max_lin_speed

        # Up/Down
        if left_gesture == "Thumb_Up" and right_gesture == "Thumb_Up":
            cmd_vel.linear.z = self.max_lin_speed
        elif left_gesture == "Thumb_Down" and right_gesture == "Thumb_Down":
            cmd_vel.linear.z = -self.max_lin_speed

        # Rotation left/right
        if left_gesture == "Thumb_Up" and right_gesture == "Closed_Fist":
            cmd_vel.angular.z = -self.max_lin_speed
        elif left_gesture == "Closed_Fist" and right_gesture == "Thumb_Up":
            cmd_vel.angular.z = self.max_lin_speed

        return cmd_vel

    def takeoff(self) -> None:
        self.takeoff_pub.publish(Empty())

    def land(self) -> None:
        self.land_pub.publish(Empty())

    def flip(self) -> None:
        msg = FlipControl()
        choice = random.choice(["left", "right", "back"])
        # Not using forward since it can be dangerous

        if choice == "left":
            msg.flip_left = True
        elif choice == "right":
            msg.flip_right = True
        elif choice == "forward":
            msg.flip_forward = True
        elif choice == "back":
            msg.flip_backward = True

        self.flip_pub.publish(msg)

    def move(self, cmd: Twist) -> None:
        self.cmd_pub.publish(cmd)

    def update(self) -> py_trees.common.Status:
        if self.last_landmark_recv is None:
            return py_trees.common.Status.FAILURE

        landmark_msg = self.last_landmark_recv

        if self.can_takeoff(landmark_msg):
            self.takeoff()
            return py_trees.common.Status.SUCCESS

        if self.can_land(landmark_msg):
            self.land()
            return py_trees.common.Status.SUCCESS

        if self.can_flip(landmark_msg):
            self.flip()
            return py_trees.common.Status.SUCCESS

        mouvement = self.build_move(landmark_msg)
        if mouvement is None:
            return py_trees.common.Status.FAILURE

        self.move(mouvement)
        return py_trees.common.Status.SUCCESS
