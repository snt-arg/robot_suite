import py_trees
from typing import Dict, Any
from robot_bt.behaviours.shared.actions import Action
from math import pi


class IsRotationComplete(py_trees.behaviour.Behaviour):

    def __init__(self, name: str, rotation_action: Action) -> None:
        super().__init__(name)
        self.rotation_action = rotation_action
        self.total_rotated_angle = None

    def setup(self):
        # self.blackboard = py_trees.blackboard.Client(name="Global")
        pass

    def update(self):
        actions: Dict["str", Any] = self.rotation_action._global_blackboard.actions
        if actions.get("rotate_robot") is None:
            return py_trees.common.Status.RUNNING
        else:
            if actions["rotate_robot"].get("total_rotated_angle") is not None:
                self.total_rotated_angle = actions["rotate_robot"][
                    "total_rotated_angle"
                ]

        if (
            self.total_rotated_angle > 2 * pi
        ):  # if the rotation is equal to 360° then, the rotation is complete
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE
