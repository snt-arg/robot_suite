import py_trees


class IsTrackingModeCorrect(py_trees.behaviour.Behaviour):

    def __init__(self, name: str, plugin_name: str) -> None:
        super().__init__(name)
        self.plugin_name = plugin_name

    def setup(self):
        self.blackboard = py_trees.blackboard.Client(name="PluginsBlackboard")
        self.blackboard.register_key(
            "tracking_mode", access=py_trees.common.Access.READ
        )

    def update(self):
        tracking_mode = self.blackboard.tracking_mode

        if (
            tracking_mode.lower() == "llm"
            and self.plugin_name.lower() == "associator_node"
        ):
            return py_trees.common.Status.SUCCESS

        elif (
            tracking_mode.lower() == "hand"
            and self.plugin_name.lower() == "landmark_detector_node"
        ):
            return py_trees.common.Status.SUCCESS

        else:
            return py_trees.common.Status.FAILURE
