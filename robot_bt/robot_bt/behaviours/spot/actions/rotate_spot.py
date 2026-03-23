# for handling ROS node
import rclpy

from rclpy.node import Publisher
from robot_bt.behaviours.shared.actions import Action


# ROS Twist message import. This message type is used to send commands to the drone.
from geometry_msgs.msg import Twist

from typing import Any, Dict

import py_trees

from math import pi


##NB : all directions : left, right... are from the drone's perspective


class RotateSpot(Action):

    # publishers
    publisher_commands: Publisher

    rotation_speed = None  # float

    rotation_angle = None  # float

    rotation_direction: str = None  # left or right

    commands_topic: str = "/byte/cmd_vel"

    def setup(self) -> None:
        self.publisher_commands = self.node.create_publisher(
            Twist, self.commands_topic, 10
        )

    def update(self):

        actions: Dict["str", Any] = self._global_blackboard.actions
        if actions.get("rotate_robot") is None:
            self.node.get_logger().error("The rotation infos are not yet available!")
            return py_trees.common.Status.FAILURE
        else:
            self.node.get_logger().debug(
                "\n*Trying to read the infos from the blackboard*\n"
            )
            if actions["rotate_robot"].get("rotation_direction") is not None:
                self.rotation_direction = actions["rotate_robot"]["rotation_direction"]

            if actions["rotate_robot"].get("rotation_angle") is not None:
                self.rotation_angle = actions["rotate_robot"]["rotation_angle"]

            if actions["rotate_robot"].get("rotation_speed") is not None:
                self.rotation_speed = actions["rotate_robot"]["rotation_speed"]

            self.node.get_logger().debug(
                f"Updated info after potential read from the blackboard:\nDirection : {self.rotation_direction}\nTarget angle : {self.rotation_angle}\nSpeed : {self.rotation_speed}\n"
            )

        if (
            self.rotation_direction is not None
            and self.rotation_angle is not None
            and self.rotation_speed is not None
        ):
            self.commands_callback()
            self.rotation_direction = None
            self.rotation_angle = None
            self.rotation_speed = None
            return py_trees.common.Status.SUCCESS

        else:
            self.node.get_logger().error(
                f"Some rotation information are missing to rotate.\nCurrent values are:\nDirection : {self.rotation_direction}\nTarget angle : {self.rotation_angle}\nSpeed : {self.rotation_speed}\n"
            )
            return py_trees.common.Status.RUNNING

    ######################### Publisher #####################################################################################################
    def commands_callback(self):

        if self.rotation_direction == "left":
            self.rotation(self.rotation_speed, -self.rotation_angle)
        elif self.rotation_direction == "right":
            self.rotation(-self.rotation_speed, self.rotation_angle)
        else:
            self.node.get_logger().error(
                f"Invalid rotation direction: {self.rotation_direction}. Rotation direction should be either 'left' or 'right'."
            )

    def rotation(self, angular_speed, target_angle) -> None:
        """Function to send rotation commands to the drone.
        Returns True if the drone did a complete rotation (no one was found) and False else
        """
        commands_msg = Twist()
        current_angle = 0
        commands_msg.angular.z = angular_speed

        self.node.get_logger().debug(
            f"Rotating action : Before rotating,  angular.z is {commands_msg.angular.z} and current_angle is {current_angle}"
        )

        t0 = self.node.get_clock().now()

        while abs(current_angle) <= abs(target_angle):

            self.publisher_commands.publish(commands_msg)
            t1 = self.node.get_clock().now()

            current_angle = commands_msg.angular.z * ((t1 - t0).to_msg().sec)

        self.node.get_logger().debug(
            f"Rotating action : After rotating ,angular.z is {commands_msg.angular.z} and current_angle is {current_angle}"
        )
