import json
from typing import Dict
import py_trees
from robot_interfaces.srv import PluginInterface
from rclpy.node import Node
from rclpy.client import Client
from rclpy.logging import rclpy

STATUS_MAP = ["FAILURE", "RUNNING", "SUCCESS"]


class PluginClient(py_trees.behaviour.Behaviour):
    """Behaviour which uses ros2 services to control a plugin

    Use this class in case you want to tick a plugin which inherits
    the PluginBase class
    """

    client: Client
    _global_blackboard: py_trees.blackboard.Client

    def __init__(self, name: str, plugin_name: str, bt_node: Node):
        super().__init__(name)
        self.plugin_name = plugin_name
        self.node = bt_node

        self._global_blackboard = py_trees.blackboard.Client(name="Global")
        self._global_blackboard.register_key("actions", py_trees.common.Access.WRITE)
        self._global_blackboard.register_key("plugins", py_trees.common.Access.WRITE)


    def setup(self) -> None:  # type: ignore
        self.client = self.node.create_client(
            PluginInterface, f"{self.plugin_name}/bt_server"
        )

    def _send_tick(self) -> PluginInterface.Response | None:
        """Requests plugin to be ticked"""
        if not self.client.service_is_ready():
            self.node.get_logger().warning(
                f"Service {self.plugin_name}/bt_server is not ready. Not ticking."
            )
            return None

        request = PluginInterface.Request()

        request.blackboard = self._serialize_blackboard()

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self.node, future)

        return future.result()

    def update(self) -> py_trees.common.Status:
        if self.client is None:
            self.node.get_logger().error("Make sure you have called setup method")
            return py_trees.common.Status.INVALID

        response = self._send_tick()

        if response is None:
            return py_trees.common.Status.FAILURE

        self._deserialize_blackboard(response.blackboard)

        return py_trees.common.Status(STATUS_MAP[response.status])

    def _serialize_blackboard(self) -> str:
        if not self._global_blackboard.exists("actions"):
            self._global_blackboard.set("actions", {})
        actions = self._global_blackboard.get("actions")

        encoded_blackboard = json.dumps(actions)

        return encoded_blackboard


    def _deserialize_blackboard(self, encoded_blackboard: str) -> None:
        print(encoded_blackboard)
        blackboard = json.loads(encoded_blackboard)
        # TODO: Make a union of received blackboard with current blackboard

        self._global_blackboard.set("actions", blackboard)
