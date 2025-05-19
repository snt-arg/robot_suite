import inspect
from abc import abstractmethod
from typing import Any, Optional
from typing_extensions import deprecated
from rclpy.node import Node
from robot_interfaces.srv import PluginInterface
import rclpy
from enum import Enum
import json


class NodeState(Enum):
    FAILURE = 0
    RUNNING = 1
    SUCCESS = 2
    INVALID = 3


class PluginNode(Node):
    tick_rate: int = 30
    standalone: bool = False

    def __init__(self, node_name: str) -> None:
        """Constructor of the class PluginBase.

        Args:
            - node_name(str): name for the ROS node
        """
        super().__init__(node_name)
        self.plugin_name = node_name

        self._read_base_params()

        if self.standalone:
            self.tick_timer = self.create_timer(1 / self.tick_rate, self._tick_callback)

        # Action server object which will control when the plugin runs
        self._server = self.create_service(
            PluginInterface, f"{node_name}/bt_server", self._service_callback
        )

    def _read_base_params(self) -> None:
        self.declare_parameter("tick_rate", self.tick_rate)
        self.declare_parameter("standalone", self.standalone)

        self.tick_rate = (
            self.get_parameter("tick_rate").get_parameter_value().integer_value
        )
        self.standalone = (
            self.get_parameter("standalone").get_parameter_value().bool_value
        )

    def _tick_callback(self) -> None:
        """Callback method for the tick_timer."""
        try:
            self.tick()
        except Exception as e:
            self.get_logger().error(f"Tick Method has failed to run with {e}")

    def _service_callback(
        self, request: PluginInterface.Request, response: PluginInterface.Response
    ) -> PluginInterface.Response:
        """
        Handles incoming action requests to control the node's state.

        This method is triggered by the action requests from the BT_server to
        control the state of the node. It sends the node's current state to the
        server, allowing the server to initiate any fallback procedures if needed.
        Then, it processes the request, updates the node's status, and sends the
        updated status and blackboard data back in the response. This method
        should not be modified.

        Parameters:
            request (PluginServer.Request): The incoming request containing
                action details and the serialized blackboard data for the node.
            response (PluginServer.Response): The response object that will be
                populated with the current node status and updated blackboard
                data before returning to the client.

        Returns:
            PluginServer.Response: The populated response object containing:
                - `status`: The current state of the node after executing `tick`.
                - `blackboard`: The serialized blackboard data updated based
                  on the action request.

        Behavior:
            - Logs the received action request and the resulting node status.
            - Deserializes the blackboard data from the request.
            - Executes the `tick` method using the provided blackboard data to
              determine the new node state.
            - Updates the response with the node's new status and serialized
              blackboard data for returning to the BT_server.
        """

        blackboard = self._deserialize_blackboard(request.blackboard)

        try:
            status = self.tick(blackboard)
        except Exception as e:
            self.get_logger().debug(
                f"Plugin <{self.plugin_name}> has failed to tick. Reason {e}"
            )
            status = NodeState.FAILURE

        self.get_logger().debug(f"Plugin <{self.plugin_name}> status: {status}")

        response.status = status.value
        response.blackboard = self._serialize_blackboard(blackboard)

        return response

    def _deserialize_blackboard(
        self, request_blackboard: str
    ) -> dict["str", Any] | None:
        self.get_logger().debug(
            f"Deserializing received blackboard: {request_blackboard}"
        )
        blackboard = None
        try:
            blackboard = json.loads(request_blackboard)
        except json.decoder.JSONDecodeError as e:
            self.get_logger().warning(f"Failed to deserialize received blackboard: {e}")
        return blackboard

    def _serialize_blackboard(self, blackboard: dict["str", Any] | None) -> str:
        self.get_logger().debug(f"Serializing blackboard: {blackboard}")
        serialized_blackboard = "{}"
        try:
            serialized_blackboard = json.dumps(blackboard)
        except TypeError as e:
            self.get_logger().warning(f"Failed to serialize blackboard: {e}")
        return serialized_blackboard

    @abstractmethod
    def tick(self, blackboard: Optional[dict["str", Any]] = None) -> NodeState:
        """
        Execute the main behavior of the node.

        This method defines the core functionality of the node and must be
        implemented in subclasses to specify the behavior of the node. The `tick`
        method is called at the rate defined by `tick_rate` when standalone mode
        is active.

        Parameters:
            blackboard (Optional[dict[str, Any]]): A dictionary representing the
                blackboard, containing shared data that the node can access and
                potentially modify. If no blackboard data is provided, this parameter
                will be `None`.

        Returns:
            NodeState: The resulting state of the node after the tick execution.
                Common values are `SUCCESS`, `FAILURE`, or `RUNNING`.

        Note:
            This is an abstract method and must be implemented in any subclass.
        """
        pass


@deprecated(
    "PluginBase will be deprecated on version 2.0. Please use PluginNode instead"
)
class PluginBase(Node):
    tick_rate: int = 30
    standalone: bool = False

    def __init__(self, node_name: str) -> None:
        """Constructor of the class PluginBase.

        Args:
            - node_name(str): name for the ROS node
        """
        super().__init__(node_name)
        self.plugin_name = node_name

        self._read_base_params()

        if self.standalone:
            self.tick_timer = self.create_timer(1 / self.tick_rate, self._tick_callback)

        # Action server object which will control when the plugin runs
        self._server = self.create_service(
            PluginInterface, f"{node_name}/bt_server", self._service_callback
        )

    def _read_base_params(self) -> None:
        self.declare_parameter("tick_rate", self.tick_rate)
        self.declare_parameter("standalone", self.standalone)

        self.tick_rate = (
            self.get_parameter("tick_rate").get_parameter_value().integer_value
        )
        self.standalone = (
            self.get_parameter("standalone").get_parameter_value().bool_value
        )

    def _tick_callback(self) -> None:
        """Callback method for the tick_timer."""
        try:
            self.tick()
        except Exception as e:
            self.get_logger().error(f"Tick Method has failed to run with {e}")

    def _service_callback(
        self, request: PluginInterface.Request, response: PluginInterface.Response
    ) -> PluginInterface.Response:
        """
        Handles incoming action requests to control the node's state.

        This method is triggered by the action requests from the BT_server to
        control the state of the node. It sends the node's current state to the
        server, allowing the server to initiate any fallback procedures if needed.
        Then, it processes the request, updates the node's status, and sends the
        updated status and blackboard data back in the response. This method
        should not be modified.

        Parameters:
            request (PluginServer.Request): The incoming request containing
                action details and the serialized blackboard data for the node.
            response (PluginServer.Response): The response object that will be
                populated with the current node status and updated blackboard
                data before returning to the client.

        Returns:
            PluginServer.Response: The populated response object containing:
                - `status`: The current state of the node after executing `tick`.
                - `blackboard`: The serialized blackboard data updated based
                  on the action request.

        Behavior:
            - Logs the received action request and the resulting node status.
            - Deserializes the blackboard data from the request.
            - Executes the `tick` method using the provided blackboard data to
              determine the new node state.
            - Updates the response with the node's new status and serialized
              blackboard data for returning to the BT_server.
        """

        # Send the current state before setting new state
        # This way, if the node fails, the BT will now and start its fallback
        # procedure

        blackboard = self._deserialize_blackboard(request.blackboard)

        if len(inspect.signature(self.tick).parameters) == 0:
            self.get_logger().warning(
                'tick() will be deprecated. Please change your tick method signature to <def tick(self, blackboard: Optional[dict["str", Any]] = None)>',
            )
            status = self.tick()
        else:
            status = self.tick(blackboard)

        self.get_logger().debug(f"Plugin <{self.plugin_name}> status: {status}")

        response.status = status.value
        response.blackboard = self._serialize_blackboard(blackboard)

        return response

    def _deserialize_blackboard(
        self, request_blackboard: str
    ) -> dict["str", Any] | None:
        self.get_logger().debug(
            f"Deserializing received blackboard: {request_blackboard}"
        )
        blackboard = None
        try:
            blackboard = json.loads(request_blackboard)
        except json.decoder.JSONDecodeError as e:
            self.get_logger().warning(f"Failed to deserialize received blackboard: {e}")
        return blackboard

    def _serialize_blackboard(self, blackboard: dict["str", Any] | None) -> str:
        self.get_logger().debug(f"Serializing blackboard: {blackboard}")
        serialized_blackboard = "{}"
        try:
            serialized_blackboard = json.dumps(blackboard)
        except TypeError as e:
            self.get_logger().warning(f"Failed to serialize blackboard: {e}")
        return serialized_blackboard

    @abstractmethod
    def tick(self, blackboard: Optional[dict["str", Any]] = None) -> NodeState:
        """
        Execute the main behavior of the node.

        This method defines the core functionality of the node and must be
        implemented in subclasses to specify the behavior of the node. The `tick`
        method is called at the rate defined by `tick_rate` when standalone mode
        is active.

        Parameters:
            blackboard (Optional[dict[str, Any]]): A dictionary representing the
                blackboard, containing shared data that the node can access and
                potentially modify. If no blackboard data is provided, this parameter
                will be `None`.

        Returns:
            NodeState: The resulting state of the node after the tick execution.
                Common values are `SUCCESS`, `FAILURE`, or `RUNNING`.

        Note:
            This is an abstract method and must be implemented in any subclass.
        """
        pass


def main():
    rclpy.init()
    node = PluginNode("test_plugin_node")

    def tick_dummy(blackboard):
        print("Ticking...")
        blackboard["land_action"] = {"topic_name":"/newName"}
        return NodeState.SUCCESS

    node.tick = tick_dummy  # type: ignore
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
