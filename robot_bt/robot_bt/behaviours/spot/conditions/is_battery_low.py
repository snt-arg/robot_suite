from robot_bt.behaviours.shared.actions import Action
import py_trees

from spot_msgs.msg import BatteryStateArray


class IsBatteryLow(Action):
    battery_topic: str = "/byte/status/battery_states"
    low_battery_threshold: float = 20

    def setup(self) -> None:
        self.current_battery = -1
        self.battery_sub = self.node.create_subscription(
            BatteryStateArray, self.battery_topic, self.battery_callback, 1
        )

    def battery_callback(self, msg: BatteryStateArray):
        self.current_battery = sum([state.charge_percentage for state in msg.battery_states])/len(msg.battery_states)

    def update(self) -> py_trees.common.Status:
        if self.current_battery < self.low_battery_threshold:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


# Link for a Spot example using Spot-specific code for the battery state:
# https://github.com/bdaiinstitute/spot_ros2/blob/main/spot_examples/spot_examples/wasd.py
