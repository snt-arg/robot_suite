"""Default BT which can be used as an example.

This BT first checks the the drone is on the same network,
then checks if it has enough battery, it has a remote remote_operator
to toggle which plugin to run and finally the hand_gestures plugin.

This is how the tree looks like:

[-] DefaultBT [✕]
    [o] DroneConnection [✕]
        --> IsDroneConnected [✕]
    [o] BatteryChecker [-]
        --> IsBatteryLow [-]
        -^- LandActionInverter [-]
            --> LandAction [-]
    --> RemoteOperator [-]
    [o] Plugins [-]
        {-} HandGesturesControl [-]
            --> CanRunHandGestures [-]
            --> HandGesturesPlugin [-]
"""

import py_trees
from rclpy.node import Node
from robot_bt.behaviours.tello.actions import (
    LandAction,
    RemoteOperator,
    GesturesInterpreterAction,
)
from robot_bt.behaviours.tello.actions.rotate_tello import RotateTello
from robot_bt.behaviours.shared.actions import PluginClient
from robot_bt.behaviours.shared.conditions import CanRunPlugin, IsBatteryLow
from robot_bt.behaviours.shared.conditions.is_tracking_mode_correct import (
    IsTrackingModeCorrect,
)
from robot_bt.behaviours.shared.conditions.is_rotation_complete import (
    IsRotationComplete,
)
from robot_bt.behaviours.tello.conditions import IsDroneConnected


class TelloBT(py_trees.composites.Sequence):
    def __init__(
        self,
        node: Node,
    ):
        super().__init__("PersonTrackingBT", memory=False)
        self.node = node

        self.build_tree()

    def setup(self):  # type: ignore
        self.plugins_blackboard = py_trees.blackboard.Client(name="PluginsBlackboard")
        self.plugins_blackboard.register_key(
            "selected_plugin", access=py_trees.common.Access.WRITE
        )
        self.plugins_blackboard.register_key(
            "tracking_mode", access=py_trees.common.Access.WRITE
        )

        self.plugins_blackboard.selected_plugin = (
            "person_tracking"  # or "landmark_detector_node"
        )

        self.plugins_blackboard.tracking_mode = "hand"  # or "llm"

    def build_tree(self):
        drone_connection = py_trees.composites.Selector(
            "DroneConnection",
            memory=False,
            children=[
                IsDroneConnected("IsDroneConnected"),
            ],
        )

        battery_checker = py_trees.composites.Selector(
            "BatteryChecker",
            memory=False,
            children=[
                py_trees.decorators.Inverter(
                    "IsBAtteryLowInverter", IsBatteryLow("IsBatteryLow", self.node)
                ),
                py_trees.decorators.Inverter(
                    "LandActionInverter", LandAction("LandAction", self.node)
                ),
            ],
        )

        remote_operator = RemoteOperator("RemoteOperator", self.node)

        plugins = py_trees.composites.Selector(
            "Plugins",
            memory=False,
            children=[
                py_trees.composites.Sequence(
                    "HandGesturesControl",
                    memory=False,
                    children=[
                        CanRunPlugin("CanRunHandGestures", "landmark_detector_node"),
                        PluginClient(
                            "HandGesturesPlugin", "landmark_detector_node", self.node
                        ),
                        py_trees.composites.Selector(
                            "GesturesInterpreterControl",
                            memory=False,
                            children=[
                                GesturesInterpreterAction(
                                    "GesturesInterpreterAction",
                                    self.node,
                                    False,
                                ),
                                py_trees.behaviours.Success("SuccessDummy"),
                            ],
                        ),
                    ],
                ),
                ## Person Tracking Plugin
                py_trees.composites.Sequence(
                    "PersonTrackingControl",
                    memory=False,
                    children=[
                        CanRunPlugin("CanRunPersonTracking", "person_tracking"),
                        PluginClient(
                            "ObjectDetectorPlugin", "object_detection_node", self.node
                        ),
                        py_trees.composites.Selector(
                            "CorrectModeControl",
                            memory=False,
                            children=[
                                py_trees.composites.Sequence(
                                    "LLMMode",
                                    memory=False,
                                    children=[
                                        IsTrackingModeCorrect(
                                            "CheckLLMMode",
                                            "associator_node",
                                        ),
                                        PluginClient(
                                            "PersonObjectAssociatorPlugin",
                                            "associator_node",
                                            self.node,
                                        ),
                                    ],
                                ),
                                py_trees.composites.Sequence(
                                    "HandMode",
                                    memory=False,
                                    children=[
                                        IsTrackingModeCorrect(
                                            "CheckHandMode", "landmark_detector_node"
                                        ),
                                        PluginClient(
                                            "HandGesturesPlugin",
                                            "landmark_detector_node",
                                            self.node,
                                        ),
                                        PluginClient(
                                            "SignFilterPlugin",
                                            "sign_filter_node",
                                            self.node,
                                        ),
                                        py_trees.composites.Selector(
                                            "GesturesInterpreterControlTracking",
                                            memory=False,
                                            children=[
                                                GesturesInterpreterAction(
                                                    "GesturesInterpreterTargetOnly",
                                                    self.node,
                                                    True,
                                                ),
                                                py_trees.behaviours.Success(
                                                    "SuccessDummy2"
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        py_trees.composites.Selector(
                            "TrackingBehaviours",
                            memory=False,
                            children=[
                                py_trees.composites.Sequence(
                                    "FollowingControl",
                                    memory=False,
                                    children=[
                                        PluginClient(
                                            "TrackerPlugin",
                                            "tracker_node",
                                            self.node,
                                        ),
                                        PluginClient(
                                            "CommandsPlugin",
                                            "following_commands_node",
                                            self.node,
                                        ),
                                    ],
                                ),
                                py_trees.composites.Sequence(
                                    "RotationControl",
                                    memory=False,
                                    children=[
                                        IsRotationComplete(
                                            "IsRotationComplete",
                                            RotateTello("dummy", self.node),
                                        ),
                                        LandAction("LandPersonLost", self.node),
                                    ],
                                ),
                                RotateTello("RotateTello", self.node),
                            ],
                        ),
                    ],
                ),
                ## end Person Tracking Plugin
            ],
        )

        # self.add_children([drone_connection, battery_checker, remote_operator, plugins])

        # test
        self.add_children([remote_operator, plugins])
        # self.add_children([drone_connection, battery_checker, remote_operator])
        # test


def bootstrap(ros_node: Node) -> py_trees.behaviour.Behaviour:
    return TelloBT(ros_node)
