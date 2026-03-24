import rclpy
from robot_bt.behaviours.shared.actions import Action
from std_srvs.srv import Trigger
import py_trees


class SitAction(Action):
    """
    Tell Spot to sit when invoked by the BT.
    """

    def __init__(self, node: rclpy.node.Node, name: str = "SitAction"):
        super().__init__(node, name)

        self.sit_client = self.node.create_client(Trigger, "/byte/sit")

    def update(self) -> py_trees.common.Status:
        try:
            self.sit_client.call_async(Trigger.Request())
            return py_trees.common.Status.SUCCESS
        except Exception as exc:
            self.node.get_logger().error(f"Sit failed: {exc}")
            return py_trees.common.Status.SUCCESS
