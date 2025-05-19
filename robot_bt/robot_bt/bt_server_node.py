from collections import defaultdict
import time
import py_trees
from py_trees.trees import BehaviourTree
from py_trees.blackboard import Client
from rclpy import Optional
from rclpy.logging import rclpy
from rclpy.node import Node
from robot_bt.bootstrap import bootstrap_bt


class BtServerNode(Node):
    _bt_tick_freq: int = 60  # Hz
    _bt_name: str = "simple_bt"
    _stop_on_failure: bool = False
    bt: Optional[BehaviourTree]
    _global_blackboard: Client

    def __init__(self, node_name):
        super().__init__(node_name)

        self.declare_params()
        self.read_params()

        self._global_blackboard = Client(name="Global")
        self._global_blackboard.register_key("plugins", py_trees.common.Access.WRITE)
        self._global_blackboard.register_key("actions", py_trees.common.Access.WRITE)

        self._global_blackboard.plugins = dict({})
        self._global_blackboard.actions = dict({})

        try:
            self.get_logger().info(f"Trying to bootstrap {self._bt_name} BT")
            bootstrap_fn = bootstrap_bt(self._bt_name)
            self.get_logger().info(f"{self._bt_name} has been bootstrapped")
            self.bt = BehaviourTree(root=bootstrap_fn(self))
            self.bt.root.attach_blackboard_client("Global")
            self.bt.setup()
        except:
            self.get_logger().error(f"Unable to bootstrap BT -> {self._bt_name}")
            self.bt = None

    def declare_params(self):
        self.declare_parameter("bt_name", self._bt_name)
        self.declare_parameter("tick_freq", self._bt_tick_freq)
        self.declare_parameter("stop_on_failure", self._stop_on_failure)
        self.declare_parameter("plugins", [])

    def read_params(self):
        self._bt_name = self.get_parameter("bt_name").get_parameter_value().string_value
        self._bt_tick_freq = (
            self.get_parameter("tick_freq").get_parameter_value().integer_value
        )
        self._stop_on_failure = (
            self.get_parameter("stop_on_failure").get_parameter_value().bool_value
        )

    def print_tree(self, tree: BehaviourTree):
        print(py_trees.display.unicode_tree(root=tree.root, show_status=True))
        print(self._global_blackboard)

    def run(self):
        while rclpy.ok():
            if self.bt is None:
                self.get_logger().error(
                    "Behaviour Tree was not successfully bootstrapped. No BT to run! Trying again in 5 seconds..."
                )
                time.sleep(5)
                continue
            try:
                self.bt.tick(post_tick_handler=self.print_tree)
            except Exception as e:
                self.get_logger().error(
                    f"A problem occured while ticking BT. Root Cause: {e}"
                )
                break
            if (
                self.bt.root.status == py_trees.common.Status.FAILURE
                and self._stop_on_failure
            ):
                break
            rclpy.spin_once(self, timeout_sec=1)
            time.sleep(1 / self._bt_tick_freq)

        if self.bt:
            self.get_logger().info("Shutting down BT")
            self.bt.shutdown()


def main():
    rclpy.init()
    node = BtServerNode("bt_server")

    node.run()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
