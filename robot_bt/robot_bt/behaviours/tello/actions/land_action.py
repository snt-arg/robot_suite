from typing import Any, Dict
from rclpy.node import Publisher
from robot_bt.behaviours.shared.actions import Action
from std_msgs.msg import Empty
import py_trees


class LandAction(Action):
    land_pub: Publisher

    def setup(self) -> None:  # type: ignore
        actions: Dict["str", Any] = self._global_blackboard.actions
        
        if actions.get("land_action") is None:
            actions["land_action"] = {"topic_name": "/land"}

        topic_name = actions["land_action"]["topic_name"]
        self.node.get_logger().info(f"Read topic_name parameter from blackboard. Value is {topic_name}")

        self.land_pub = self.node.create_publisher(Empty, topic_name, 1)


    def update(self) -> py_trees.common.Status:
        self.land_pub.publish(Empty())
        return py_trees.common.Status.SUCCESS
