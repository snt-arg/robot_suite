from robot_bt.behaviours.shared.actions import Action
import py_trees

from std_msgs.msg import String


class RemoteOperator(Action):
    keyboard_topic: str = "/key_pressed"

    def setup(self) -> None:  # type: ignore
        self.key_pressed = ""
        self.key_press_sub = self.node.create_subscription(
            String, self.keyboard_topic, self.key_pressed_callback, 1
        )

        self.blackboard = py_trees.blackboard.Client(name="PluginsBlackboard")
        self.blackboard.register_key(
            "selected_plugin", access=py_trees.common.Access.WRITE
        )

    def key_pressed_callback(self, msg: String):
        self.key_pressed = msg.data

    def update(self) -> py_trees.common.Status:
        for key in self.key_pressed.split():
            if key == "m" or key == "s":  # m for manual control, s for stop tracking
                self.blackboard.selected_plugin = ""
            elif key == "h":
                self.blackboard.selected_plugin = "landmark_detector_node"
            elif key == "t":
                self.blackboard.selected_plugin = "person_tracking"

        return py_trees.common.Status.SUCCESS
