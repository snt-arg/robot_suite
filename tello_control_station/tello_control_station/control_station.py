from rclpy.node import Node
from std_msgs.msg import String, Empty, Bool, Float32
from sensor_msgs.msg import Image
from tello_msgs.msg import FlightStats
from geometry_msgs.msg import Twist
from plugin_base.plugin_base import NodeState
from tello_control_station.interface import Interface, matching_keys
import math
from typing import Union, Tuple
import json
import threading
import subprocess
from ament_index_python import get_package_prefix


class ControlStation(Node):
    def __init__(self) -> None:
        super().__init__("remote_controller")

        self.control_mode = "k"
        self.click_pos = None
        self.face_list = []
        self.nlp_pid = None

        # Topics
        self.key_pressed_publisher_topic_name = ""
        self.cmd_vel_publisher_topic_name = ""
        self.battery_subscriber_topic_name = ""
        self.cam_image_subscriber_topic_name = ""
        self.takeoff_publisher_topic_name = ""
        self.land_publisher_topic_name = ""
        self.skeleton_layer_subscriber_topic_name = "/hand/annotated/image"

        self.read_prameters()
        self.init_publishers()
        self.init_subsciptions()
        self.init_timers()

        self.pg_interface = Interface()

    def init_publishers(self):
        self.key_pressed_publisher = self.create_publisher(
            String, self.key_pressed_publisher_topic_name, 10
        )
        self.cmd_vel_publisher = self.create_publisher(
            Twist, self.cmd_vel_publisher_topic_name, 1
        )
        self.takeoff_publisher = self.create_publisher(
            Empty, self.takeoff_publisher_topic_name, 1
        )
        self.land_publisher = self.create_publisher(
            Empty, self.land_publisher_topic_name, 1
        )

    def init_subsciptions(self):
        self.battery_subscriber = self.create_subscription(
            FlightStats,
            self.battery_subscriber_topic_name,
            self._update_battery,
            10,
        )
        self.cam_image_subscriber = self.create_subscription(
            Image, self.cam_image_subscriber_topic_name, self._update_bg, 1
        )
        self.skeleton_layer_subscriber = self.create_subscription(
            Image,
            self.skeleton_layer_subscriber_topic_name,
            self._update_sekeleton_layer,
            1,
        )
        self.nlp_command_subscriber = self.create_subscription(
            String, "/switch_mode", self.switch_mode, 10
        )

    def init_timers(self):
        self.timer = self.create_timer(1 / 30, self.tick)

    def _update_battery(self, msg: FlightStats):
        self.pg_interface.update_battery(msg.battery_percentage)

    def tick(self):
        self.pg_interface.tick()
        self.get_keyboard_input()
        self.get_joystick_input()

    def get_nlp_input(self, mode_command: str):
        print(mode_command)
        msg = String()
        if mode_command == "keyboard":
            self.pg_interface.update_display_mode("m")
            self.control_mode = "k"
            # msg.data = "m"
            # self.key_pressed_publisher.publish(msg)
            self.get_logger().info("control mode switched to keyboard")
            return NodeState.SUCCESS
        elif mode_command == "hand":
            self.control_mode = "h"
            self.get_logger().info(f"Control mode set to {self.control_mode}")
            self.pg_interface.update_display_mode("h")
            # msg.data = "h"
            # self.key_pressed_publisher.publish(msg)
            self.get_logger().info("control mode switched to hand")
            return NodeState.SUCCESS

        else:
            self.get_logger().warning(f"Unrecognized mode command: {mode_command}")

    def switch_mode(self, msg: String):
        mode = msg.data
        if mode:
            self.get_nlp_input(mode)
        else:
            self.get_logger().warning("Empty mode received in switch_mode")

    def get_keyboard_input(self):
        keys = self.pg_interface.get_key_pressed()

        # START/STOP
        if keys[matching_keys["t"]]:
            self.takeoff_publisher.publish(Empty())
            return NodeState.RUNNING
        if keys[matching_keys["l"]]:
            self.land_publisher.publish(Empty())
            return NodeState.RUNNING

        msg = String()

        # QUIT
        if keys[matching_keys["q"]]:
            msg.data = "q"
            self.key_pressed_publisher.publish(msg)
            return NodeState.SUCCESS
        if keys[matching_keys["e"]]:
            msg.data = "e"
            self.key_pressed_publisher.publish(msg)
            return NodeState.FAILURE

        # CHANGE CONTROL MODE
        if keys[matching_keys["j"]]:
            self.control_mode = "j"
            self.pg_interface.update_display_mode("m")
            msg.data = "m"
            self.key_pressed_publisher.publish(msg)
            self.get_logger().info("control mode switched to joystick")
            return NodeState.SUCCESS
        if keys[matching_keys["k"]]:
            self.pg_interface.update_display_mode("m")
            self.control_mode = "k"
            msg.data = "m"
            self.key_pressed_publisher.publish(msg)
            self.get_logger().info("control mode switched to keyboard")
            return NodeState.SUCCESS
        if keys[matching_keys["h"]]:
            self.control_mode = "h"
            self.pg_interface.update_display_mode("h")
            msg.data = "h"
            self.key_pressed_publisher.publish(msg)
            self.get_logger().info("control mode switched to hand")
            return NodeState.SUCCESS
        if keys[matching_keys["f"]]:
            self.control_mode = "f"
            self.pg_interface.update_display_mode("f")
            msg.data = "f"
            self.key_pressed_publisher.publish(msg)
            self.get_logger().info("control mode switched to face")
            return NodeState.SUCCESS
        if keys[matching_keys["m"]]:
            msg.data = "m"
            self.control_mode = "k"
            self.pg_interface.update_display_mode("m")
            self.key_pressed_publisher.publish(msg)
            self.get_logger().info("control mode switched to manual")
            return NodeState.SUCCESS
        if keys[matching_keys["n"]]:
            msg.data = "n"
            self.control_mode = "n"
            self.pg_interface.update_display_mode("n")
            self.key_pressed_publisher.publish(msg)
            self.get_logger().info("control switched to natural language")
            threading.Thread(target=self.nlp_terminal).start()
            return NodeState.SUCCESS

        if self.control_mode != "k":
            return NodeState.RUNNING

        # MOVEMENT
        vel_msg = Twist()

        if keys[matching_keys["w"]]:
            vel_msg.linear.x += 0.5
        if keys[matching_keys["s"]]:
            vel_msg.linear.x -= 0.5
        if keys[matching_keys["a"]]:
            vel_msg.linear.y += 0.5
        if keys[matching_keys["d"]]:
            vel_msg.linear.y -= 0.5
        if keys[matching_keys["up"]]:
            vel_msg.linear.z += 0.5
        if keys[matching_keys["down"]]:
            vel_msg.linear.z -= 0.5
        if keys[matching_keys["left"]]:
            vel_msg.angular.z += 0.5
        if keys[matching_keys["right"]]:
            vel_msg.angular.z -= 0.5
        self.cmd_vel_publisher.publish(vel_msg)

    def nlp_terminal(self):
        """
        Opens a new terminal and runs the ROSGPT client node for natural language processing.
        """

        self.get_logger().info("Starting ROSGPT client in a new terminal...")
        pkg_dir = get_package_prefix("robot_agent")
        if self.nlp_pid is None:
            self.nlp_pid = subprocess.Popen(
                [
                    "gnome-terminal",
                    "--",
                    "bash",
                    "-c",
                    f"{pkg_dir}/lib/robot_agent/robot_agent; exec bash",
                ]
            )

    def get_joystick_input(self):
        if self.control_mode != "j":
            return NodeState.RUNNING

        joysticks = self.pg_interface.get_joysticks()

        if not joysticks:
            self.control_mode = "k"
            self.get_logger().info("control mode switched to keyboard")

        for joystick in joysticks:
            if joystick.get_power_level() in ["empty", "low"]:
                self.get_logger().info("Low energy, control mode switched to keyboard")
                self.control_mode = "k"

            msg = String()

            # CHANGE CONTROL MODE
            if joystick.get_button(0):  # A
                self.control_mode = "h"
                msg.data = "h"
                self.pg_interface.update_display_mode("h")
                self.key_pressed_publisher.publish(msg)
                self.get_logger().info("control mode switched to hand")
                return NodeState.SUCCESS
            if joystick.get_button(1):  # B
                self.control_mode = "f"
                msg.data = "f"
                self.pg_interface.update_display_mode("f")
                self.key_pressed_publisher.publish(msg)
                self.get_logger().info("control mode switched to face")
                return NodeState.SUCCESS
            if joystick.get_button(2):  # X
                self.control_mode = "k"
                self.pg_interface.update_display_mode("k")
                msg.data = "m"
                self.key_pressed_publisher.publish(msg)
                self.get_logger().info("control mode switched to keyboard")
                return NodeState.SUCCESS

            if joystick.get_button(3):  # Y
                pass

            # QUIT
            if joystick.get_button(4):  # LB
                msg.data = "e"
                self.key_pressed_publisher.publish(msg)
                return NodeState.FAILURE
            if joystick.get_button(5):  # RB
                msg.data = "q"
                self.key_pressed_publisher.publish(msg)
                return NodeState.SUCCESS

            # START/STOP
            if joystick.get_button(6):  # BACK
                self.land_publisher.publish(Empty())
                return NodeState.RUNNING
            if joystick.get_button(7):  # START
                self.takeoff_publisher.publish(Empty())
                return NodeState.RUNNING

            if joystick.get_button(8):  # LOGITECH
                pass
            if joystick.get_button(9):  # LEFT ANALOG PRESS
                pass
            if joystick.get_button(10):  # RIGHT ANALOG PRESS
                pass

            msg = Twist()

            # MOVEMENT
            msg.linear.x = (
                -joystick.get_axis(4) if abs(joystick.get_axis(4)) > 0.05 else 0.0
            )
            msg.linear.y = (
                -joystick.get_axis(3) if abs(joystick.get_axis(3)) > 0.05 else 0.0
            )
            msg.linear.z = (
                -joystick.get_axis(1) if abs(joystick.get_axis(1)) > 0.05 else 0.0
            )
            msg.angular.z = (
                -joystick.get_axis(0) if abs(joystick.get_axis(0)) > 0.05 else 0.0
            )

            self.cmd_vel_publisher.publish(msg)

    def read_prameters(self):
        self.declare_parameter("cmd_topic_name", "/cmd_vel")
        self.declare_parameter("key_pressed_topic_name", "/key_pressed")
        self.declare_parameter("battery_level_topic_name", "/flight_data")
        self.declare_parameter("cam_image_topic_name", "/camera/image_raw")
        self.declare_parameter("land_topic_name", "/land")
        self.declare_parameter("takeoff_topic_name", "/takeoff")

        self.cmd_vel_publisher_topic_name = (
            self.get_parameter("cmd_topic_name").get_parameter_value().string_value
        )

        self.key_pressed_publisher_topic_name = (
            self.get_parameter("key_pressed_topic_name")
            .get_parameter_value()
            .string_value
        )

        self.battery_subscriber_topic_name = (
            self.get_parameter("battery_level_topic_name")
            .get_parameter_value()
            .string_value
        )

        self.cam_image_subscriber_topic_name = (
            self.get_parameter("cam_image_topic_name")
            .get_parameter_value()
            .string_value
        )

        self.land_publisher_topic_name = (
            self.get_parameter("land_topic_name").get_parameter_value().string_value
        )

        self.takeoff_publisher_topic_name = (
            self.get_parameter("takeoff_topic_name").get_parameter_value().string_value
        )

    def _update_bg(self, img):
        self.pg_interface.update_bg_image(img)

    def _update_face_to_follow(self, msg):
        if (
            nose := self._normalized_to_pixel_coordinates(msg.nose.x, msg.nose.y)
        ) is None:
            return

        self.pg_interface.update_boxes(msg, True, nose)

    def _update_sekeleton_layer(self, msg):
        self.pg_interface.update_skeleton_layer(msg)

    def _normalized_to_pixel_coordinates(
        self, normalized_x: float, normalized_y: float
    ) -> Union[None, Tuple[int, int]]:
        """Converts normalized value pair to pixel coordinates."""

        IMG_W, IMG_H = 960, 720

        # Checks if the float value is between 0 and 1.
        def is_valid_normalized_value(value: float) -> bool:
            return (value > 0 or math.isclose(0, value)) and (
                value < 1 or math.isclose(1, value)
            )

        if not (
            is_valid_normalized_value(normalized_x)
            and is_valid_normalized_value(normalized_y)
        ):
            # TODO: Draw coordinates even if it's outside of the image bounds.
            return None

        x_px = min(math.floor(normalized_x * IMG_W), IMG_W - 1)
        y_px = min(math.floor(normalized_y * IMG_H), IMG_W - 1)
        return (x_px, y_px)
