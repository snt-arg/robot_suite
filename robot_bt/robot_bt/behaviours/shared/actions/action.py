import py_trees
from rclpy.node import Node


class Action(py_trees.behaviour.Behaviour):
    """Default py_trees behaviour with ros2 Node

    Use this in case you need to work with anything ros2 related
    """

    _global_blackboard: py_trees.blackboard.Client

    def __init__(self, name, bt_node: Node):
        super().__init__(name)
        self.node = bt_node

        self._global_blackboard = py_trees.blackboard.Client(name="Global")
        self._global_blackboard.register_key("actions", py_trees.common.Access.WRITE)
