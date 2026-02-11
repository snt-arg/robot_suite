from rosa import RobotSystemPrompts
from langchain.agents import tool

from robot_agent.controller import Controller

from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist
from std_srvs.srv import Trigger
from spot_msgs.msg import (
    BatteryStateArray,
    Metrics,
    Feedback,
    MobilityParams,
    PowerState,
    BehaviorFaultState,
    SystemFaultState,
    WiFiState,
)
from geometry_msgs.msg import TwistWithCovarianceStamped
from sensor_msgs.msg import JointState

import time
from datetime import datetime

from typing import List, Optional
from colorama import Fore, init
import json

init(autoreset=True)


DICTIONARY_YOLO_OBJECTS = {
    24: "backpack",
    25: "umbrella",
    26: "handbag",
    39: "bottle",
    41: "cup",
    42: "fork",
    43: "knife",
    44: "spoon",
    45: "bowl",
    46: "banana",
    47: "apple",
    63: "laptop",
    66: "keyboard",
    67: "cell phone",
    73: "book",
}


class SpotController(Controller):

    ### Topics and services
    # velocity commands
    commands_topic = "/byte/cmd_vel"

    # mode switching
    key_pressed_topic = "/key_pressed"
    switch_mode_topic = "/switch_mode"

    # Status topics
    battery_state_topic = "/byte/status/battery_states"
    metrics_topic = "/byte/status/metrics"
    feedback_topic = "/byte/status/feedback"
    odometry_topic = "/byte/odometry/twist"
    mobility_topic = "/byte/status/mobility_params"
    power_state_topic = "/byte/status/power_states"
    behavior_faults_topic = "/byte/status/behavior_faults"
    system_faults_topic = "/byte/status/system_faults"
    wifi_state_topic = "/byte/status/wifi"
    joint_states_topic = "/byte/joint_states"

    # Services
    stand_service_name = "/byte/stand"
    sit_service_name = "/byte/sit"

    # tracking topics
    tracking_status_topic = "/tracking_status"  # Topic specifying whether or not the tracking is still ongoing
    tracking_signal_topic = "/tracking_signal_llm"  # Topic on which th signal to track a specific person is sent
    person_info_topic = "/tracking_info"  # Topic on which information about detected persons and objects are sent

    def __init__(self, robot_name: str = "Spot") -> None:
        super().__init__("spot_controller")

        # Publishers
        self.commands_pub = None
        self.key_pressed_pub = None
        self.switch_mode_pub = None
        self.tracking_signal_pub = None

        # subscribers
        self.battery_state_sub = None
        self.metrics_sub = None
        self.feedback_sub = None
        self.odometry_sub = None
        self.mobility_sub = None
        self.power_state_sub = None
        self.behavior_faults_sub = None
        self.system_faults_sub = None
        self.wifi_state_sub = None
        self.joint_states_sub = None
        self.person_info_sub = None
        self.tracking_status_sub = None

        # clients
        self.stand_clientnode = None
        self.sit_client = None

        # variables
        self.warned_low_battery = False

        self.battery_states = None
        self.metrics = None
        self.feedback = None
        self.odometry = None
        self.mobility_params = None
        self.power_state = None
        self.behavior_faults = None
        self.system_faults = None
        self.wifi_state = None
        self.joint_states = None

        self.robot_name = robot_name
        self.current_tracking_object = None
        self.tracking_status = None

        # Initialize ROS node
        self._init_parameters()
        self._init_publishers()
        self._init_subscriptions()
        self._init_clients()

    ########################################## Initialization Methods ############################################################################
    def _init_parameters(self) -> None:
        """Method to initialize parameters such as ROS topics' names from config file"""
        self.declare_parameter("commands_topic", self.commands_topic)
        self.declare_parameter("key_pressed_topic", self.key_pressed_topic)
        self.declare_parameter("switch_mode_topic", self.switch_mode_topic)

        self.declare_parameter("battery_state_topic", self.battery_state_topic)
        self.declare_parameter("metrics_topic", self.metrics_topic)
        self.declare_parameter("feedback_topic", self.feedback_topic)
        self.declare_parameter("odometry_topic", self.odometry_topic)
        self.declare_parameter("mobility_topic", self.mobility_topic)
        self.declare_parameter("power_state_topic", self.power_state_topic)
        self.declare_parameter("behavior_faults_topic", self.behavior_faults_topic)
        self.declare_parameter("system_faults_topic", self.system_faults_topic)
        self.declare_parameter("wifi_state_topic", self.wifi_state_topic)
        self.declare_parameter("joint_states_topic", self.joint_states_topic)

        self.declare_parameter("stand_service_name", self.stand_service_name)
        self.declare_parameter("sit_service_name", self.sit_service_name)

        self.declare_parameter("tracking_status_topic", self.tracking_status_topic)
        self.declare_parameter("tracking_signal_topic", self.tracking_signal_topic)
        self.declare_parameter("person_info_topic", self.person_info_topic)

        self.commands_topic = (
            self.get_parameter("commands_topic").get_parameter_value().string_value
        )

        self.key_pressed_topic = (
            self.get_parameter("key_pressed_topic").get_parameter_value().string_value
        )
        self.switch_mode_topic = (
            self.get_parameter("switch_mode_topic").get_parameter_value().string_value
        )

        self.battery_state_topic = (
            self.get_parameter("battery_state_topic").get_parameter_value().string_value
        )
        self.metrics_topic = (
            self.get_parameter("metrics_topic").get_parameter_value().string_value
        )
        self.feedback_topic = (
            self.get_parameter("feedback_topic").get_parameter_value().string_value
        )
        self.odometry_topic = (
            self.get_parameter("odometry_topic").get_parameter_value().string_value
        )
        self.mobility_topic = (
            self.get_parameter("mobility_topic").get_parameter_value().string_value
        )
        self.power_state_topic = (
            self.get_parameter("power_state_topic").get_parameter_value().string_value
        )
        self.behavior_faults_topic = (
            self.get_parameter("behavior_faults_topic")
            .get_parameter_value()
            .string_value
        )
        self.system_faults_topic = (
            self.get_parameter("system_faults_topic").get_parameter_value().string_value
        )
        self.wifi_state_topic = (
            self.get_parameter("wifi_state_topic").get_parameter_value().string_value
        )
        self.joint_states_topic = (
            self.get_parameter("joint_states_topic").get_parameter_value().string_value
        )

        self.stand_service_name = (
            self.get_parameter("stand_service_name").get_parameter_value().string_value
        )

        self.sit_service_name = (
            self.get_parameter("sit_service_name").get_parameter_value().string_value
        )

        self.tracking_status_topic = (
            self.get_parameter("tracking_status_topic")
            .get_parameter_value()
            .string_value
        )

        self.tracking_signal_topic = (
            self.get_parameter("tracking_signal_topic")
            .get_parameter_value()
            .string_value
        )

        self.person_info_topic = (
            self.get_parameter("person_info_topic").get_parameter_value().string_value
        )

    def _init_publishers(self) -> None:
        """Method to initialize publishers"""
        self.commands_pub = self.create_publisher(Twist, self.commands_topic, 10)
        self.key_pressed_pub = self.create_publisher(String, self.key_pressed_topic, 10)
        self.switch_mode_pub = self.create_publisher(String, self.switch_mode_topic, 10)
        self.tracking_signal_pub = self.create_publisher(
            String, self.tracking_signal_topic, 10
        )

    def _init_subscriptions(self) -> None:
        """Method to initialize subscriptions"""
        self.battery_state_sub = self.create_subscription(
            BatteryStateArray, self.battery_state_topic, self.battery_state_callback, 10
        )

        self.metrics_sub = self.create_subscription(
            Metrics, self.metrics_topic, self.metrics_callback, 10
        )

        self.feedback_sub = self.create_subscription(
            Feedback, self.feedback_topic, self.feedback_callback, 10
        )

        self.odometry_sub = self.create_subscription(
            TwistWithCovarianceStamped, self.odometry_topic, self.odometry_callback, 10
        )

        self.mobility_sub = self.create_subscription(
            MobilityParams, self.mobility_topic, self.mobility_callback, 10
        )

        self.power_state_sub = self.create_subscription(
            PowerState, self.power_state_topic, self.power_state_callback, 10
        )

        self.behavior_faults_sub = self.create_subscription(
            BehaviorFaultState,
            self.behavior_faults_topic,
            self.behavior_faults_callback,
            10,
        )

        self.system_faults_sub = self.create_subscription(
            SystemFaultState, self.system_faults_topic, self.system_faults_callback, 10
        )

        self.wifi_state_sub = self.create_subscription(
            WiFiState, self.wifi_state_topic, self.wifi_state_callback, 10
        )

        self.joint_states_sub = self.create_subscription(
            JointState, self.joint_states_topic, self.joint_states_callback, 10
        )

        self.tracking_status_sub = self.create_subscription(
            Bool, self.tracking_status_topic, self.tracking_status_callback, 10
        )

        self.person_info_sub = self.create_subscription(
            String, self.person_info_topic, self.person_info_callback, 10
        )

    def _init_clients(self) -> None:
        """Method to initialize clients for services"""
        self.stand_client = self.create_client(Trigger, self.stand_service_name)
        self.sit_client = self.create_client(Trigger, self.sit_service_name)

    ############################################## ROS Subscribers callback functions #####################################################################
    def battery_state_callback(self, msg: BatteryStateArray) -> None:
        self.battery_states = (
            msg.battery_states[0] if len(list(msg.battery_states)) > 0 else None
        )
        self.get_logger().debug(f"Battery states received: {msg}")

        if self.battery_states is not None:
            battery_percentage = self.battery_states.charge_percentage
            if battery_percentage < 20.0 and not self.warned_low_battery:
                self.warned_low_battery = True
                self.get_logger().warn(
                    f"Battery for {self.robot_name} is at {battery_percentage:.1f}%. "
                    "Robot should sit."
                )
            elif battery_percentage >= 20.0:
                self.warned_low_battery = False
        else:
            self.get_logger().warning(f"Received empty battery state list. {msg}")

    def metrics_callback(self, msg: Metrics) -> None:
        self.metrics = msg
        self.get_logger().debug(f"Metrics received: {msg}")

    def feedback_callback(self, msg: Feedback) -> None:
        self.feedback = msg
        self.get_logger().debug(f"Feedback received: {msg}")

    def odometry_callback(self, msg: TwistWithCovarianceStamped) -> None:
        self.odometry = msg
        self.get_logger().debug(f"Odometry received: {msg}")

    def mobility_callback(self, msg: MobilityParams) -> None:
        self.mobility_params = msg
        self.get_logger().debug(f"Mobility parameters received: {msg}")

    def power_state_callback(self, msg: PowerState) -> None:
        self.power_state = msg
        self.get_logger().debug(f"Power state received: {msg}")

    def behavior_faults_callback(self, msg: BehaviorFaultState) -> None:
        self.behavior_faults = msg
        self.get_logger().debug(f"Behavior faults received: {msg}")

    def system_faults_callback(self, msg: SystemFaultState) -> None:
        self.system_faults = msg
        self.get_logger().debug(f"System faults received: {msg}")

    def wifi_state_callback(self, msg: WiFiState) -> None:
        self.wifi_state = msg
        self.get_logger().debug(f"WiFi state received: {msg}")

    def joint_states_callback(self, msg: JointState) -> None:
        self.joint_states = msg
        self.get_logger().debug(f"Joint states received: {msg}")

    def person_info_callback(self, msg) -> None:
        """Callback for the subscriber node (to topic self.person_info_topic).
        Receives information about detected persons and objects.
        This callback finds a person who is associated with the target object,
        publishes their data ONCE to /tracking_signal, and then stops until a new command.
        """

        # 1. If we are not actively looking for an object, do nothing.
        if not self.current_tracking_object:
            return
        if not msg.data or not msg.data.strip():
            return

        try:
            list_of_people = json.loads(msg.data)
            if not isinstance(list_of_people, list):
                list_of_people = [list_of_people]

            for person_data in list_of_people:
                # Look inside the 'objects' list for each person
                if (
                    "info" in person_data
                    and isinstance(person_data["info"], dict)
                    and "objects" in person_data["info"]
                ):
                    held_objects = person_data["info"]["objects"]

                    # If the target object is found with this person...
                    if self.current_tracking_object in held_objects:

                        # 4. We found the compatible person! Publish their complete data.
                        self.get_logger().info(
                            f"MATCH FOUND: Sending compatible person (ID: {person_data.get('id')}) to /tracking_signal."
                        )

                        filtered_info = json.dumps(person_data)
                        self.tracking_signal_pub.publish(String(data=filtered_info))
                        self.current_tracking_object = None
                        self.tracking_confirmation_received.set()

                        break  # Stop checking other people in this message

        except Exception as e:
            self.get_logger().error(f"Error in tracking_info_callback: {e}")

    def tracking_status_callback(self, msg) -> None:
        """Callback for the subscriber node (to topic self.tracking_status_topic).
        Receives tracking status updates."""
        self.tracking_status = msg.data
        self.get_logger().debug(f"Received tracking status: {msg.data}")

    ################################################## ROS Service Clients ########################################################
    async def call_sit_service(self) -> None:
        """Method to call the sit service to make Spot sit down."""
        try:
            await self.sit_client.call_async(Trigger.Request())

        except Exception as exc:
            self.node.get_logger().error(f"Sit failed: {exc}")

    async def call_stand_service(self) -> None:
        """Method to call the stand service to make Spot stand up."""
        try:
            await self.stand_client.call_async(Trigger.Request())

        except Exception as exc:
            self.node.get_logger().error(f"Stand failed: {exc}")

    ################################################## set unknown string to "" ###################################################
    def change_unknown_to_empty(self, the_string: str):
        """Method to change the string 'unknown' to an empty string."""
        if the_string == "unknown":
            return ""
        else:
            return the_string

    ################################################## Tools for LLM Commands ########################################################
    def get_battery_status(self) -> str:
        battery_percentage_str: str = "unknown"
        remaining_runtime_str: str = "unknown"
        temperatures_str: str = "unknown"
        status_str: str = "unknown"

        if self.battery_states is not None:

            battery_percentage_str = f"The battery percentage for {self.robot_name} is currently {self.battery_states.charge_percentage}%.\n"
            remaining_runtime_str = f"The remaining runtime is estimated to {self.battery_states.estimated_runtime}.\n"
            temperatures_str = (
                f"The temperature readings are {self.battery_states.temperatures}.\n"
            )
            status_str = (
                f"The current status of the battery is {self.battery_states.status}.\n"
            )

            return (
                battery_percentage_str
                + remaining_runtime_str
                + temperatures_str
                + status_str
            )

        else:
            return f"Battery percentage for {self.robot_name} has not been reported yet or is unavailable."

    def get_mobility_metrics(self) -> str:
        total_distance_str: str = "unknown"
        total_time_moving: str = "unknown"
        physical_posture: str = "unknown"
        motion_configuration: str = "unknown"

        if self.metrics is not None:
            total_distance_str = self.change_unknown_to_empty(total_distance_str)
            total_time_moving = self.change_unknown_to_empty(total_time_moving)

            total_distance_str += f"The total distance traveled by {self.robot_name} is {self.metrics.distance:.2f} meters.\n"
            total_time_moving += f"The total time {self.robot_name} has been moving is {self.metrics.time_moving.sec} seconds.\n"

        if self.feedback is not None:
            physical_posture = self.change_unknown_to_empty(physical_posture)
            motion_configuration = self.change_unknown_to_empty(motion_configuration)

            physical_posture += f"The current physical posture of {self.robot_name} is :\nStanding : {self.feedback.standing}\nSitting:{self.feedback.sitting}.\n"
            motion_configuration += f"The motion configuration of the robot is:\nMoving : {self.feedback.moving}\n"

        if self.mobility_params is not None:
            physical_posture = self.change_unknown_to_empty(physical_posture)
            motion_configuration = self.change_unknown_to_empty(motion_configuration)

            physical_posture += f"The estimated body position and orientation (pose) relative to the world is {self.mobility_params.body_control}\n"
            motion_configuration += f"Locomotion behavior hint: {self.mobility_params.locomotion_hint}\nStair climbing: {self.mobility_params.stair_hint}.\n"

        return (
            "Total distance result: "
            + total_distance_str
            + "\nTotal moving time result: "
            + total_time_moving
            + "\nPhysical posture result: "
            + physical_posture
            + "\nMotion configuration result: "
            + motion_configuration
        )

    def get_power_state(self) -> str:
        """
        Provides the current power supply conditions.
        The information that you can get through this tool include:
          * the state of the motor and shore power systems,
          * the charge level specific to locomotion systems,
          * the estimated runtime remaining for locomotion.
          * the accumulated electrical power usage.
        """
        return "Tool to be implemented."

    def get_info_spot(self) -> str:
        """Gets the robot dog (spot) general information, such as its specie, version and nickname"""
        return "Tool to be implemented."

    def get_odometry(self) -> str:
        """Represents the robot's current estimated velocity, both linear and angular, in three dimensions."""
        return "Tool to be implemented."

    def get_faults(self) -> str:
        """
        Gets faults reports of the robot dog. There are two faults types:
        * Behavior Fault State:
            Lists any active behavior-related faults.
        * System Fault State:
            Reports both active and historical faults detected in the robot’s internal systems.
        """
        return "Tool to be implemented."

    def get_wifi_connection_state(self) -> str:
        if self.wifi_state is not None:
            mode_str = (
                "unknown"
                if self.wifi_state.current_mode is None
                else str(self.wifi_state.current_mode)
            )
            ssid_str = (
                f"Connected to SSID: {self.wifi_state.ssid}"
                if self.wifi_state.ssid
                else "unknown"
            )
            return f"Wi-Fi Mode: {mode_str}.\n SSID: {ssid_str}."
        else:
            return "Wi-Fi state has not been reported yet or is unavailable."

    def get_general_status(self) -> str:
        battery_percentage_str: str = "unknown"
        posture_str: str = "unknown"
        wifi_str: str = "unknown"

        if self.battery_states is not None:
            battery_percentage_str = f"The battery percentage for {self.robot_name} is currently {self.battery_states.charge_percentage}%.\n"

        if self.feedback is not None:
            posture_str = f"The current physical posture of {self.robot_name} is :\nStanding : {self.feedback.standing}\nSitting:{self.feedback.sitting}.\nThe motion configuration of the robot is:\nMoving : {self.feedback.moving}\n"

        if self.wifi_state is not None:
            wifi_str = (
                "unknown"
                if self.wifi_state.current_mode is None
                or self.wifi_state.current_mode == 0
                else "access point" if self.wifi_state.current_mode == 1 else "client"
            )

        tracking_info_str = (
            f" Actively tracking: '{self.current_tracking_object}'."
            if self.current_tracking_object
            else " Not currently tracking."
        )

        return (
            "Battery info :"
            + battery_percentage_str
            + "\nPosture: "
            + posture_str
            + "\nWifi: "
            + wifi_str
            + "\nTracking :"
            + tracking_info_str
        )

    def sit(self) -> str:
        # time stamp
        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] Start sit time..")

        sitting = None

        if self.feedback is not None:
            sitting: bool = self.feedback.sitting

        if sitting:
            try:
                self.call_sit_service()

                # time stamp
                time_str = datetime.now().strftime("%H:%M:%S:%f")
                print(Fore.CYAN + f"[{time_str}] End sit time..")

                return f"{self.robot_name} is sitting."
            except Exception as e:
                return f"Failed to sit {self.robot_name}: {e}"
        else:
            return f"Robot state (sitting/standing) is not yet known. Cannot sit."

    def stand(self) -> str:
        # time stamp
        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] Start stand tool time..")

        standing = None

        if self.feedback is not None:
            standing: bool = self.feedback.standing

        if standing:
            try:
                self.call_stand_service()

                time_str = datetime.now().strftime("%H:%M:%S:%f")
                print(Fore.CYAN + f"[{time_str}] End stand tool time..")

                return f"{self.robot_name} is standing."
            except Exception as e:
                return f"Failed to stand {self.robot_name}: {e}"
        else:
            return f"Robot state (sitting/standing) is not yet known. Cannot stand."

    def move(self, linear: List[float], angular: float, duration: int) -> str:
        # time stamp
        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] Start motion time..")

        standing = None

        print(
            f"linear : {type(linear)}, angular={type(angular)}, duration={type(duration)}"
        )

        if self.feedback is not None:
            standing: bool = self.feedback.standing

        if standing:

            try:
                msg_twist = Twist()
                linear_x = float(linear[0])
                linear_y = float(linear[1])
                linear_z = float(linear[2])

                msg_twist.linear.x = linear_x
                msg_twist.linear.y = linear_y
                msg_twist.linear.z = linear_z
                msg_twist.angular.z = float(angular)

                print(
                    f"DEBUG: LLM called move() with linear={linear}, angular={angular}, duration={duration}s"
                )

                t0 = self.get_clock().now().nanoseconds

                while (self.get_clock().now().nanoseconds - t0) / 1e9 <= duration:
                    print((self.get_clock().now().nanoseconds - t0) / 1e9)

                    self.commands_pub.publish(msg_twist)

                # Send a final command to stop the robot
                self.commands_pub.publish(Twist())

                # time stamp
                time_str = datetime.now().strftime("%H:%M:%S:%f")
                print(Fore.CYAN + f"[{time_str}] End motion time..")

                return f"Moved {self.robot_name} with linear={linear}, angular={angular} for {duration}s and then stopped."
            except Exception as e:
                print(f"Failed to move {self.robot_name}: {e}")
                return f"Failed to move {self.robot_name}: {e}"
        else:
            return f"Robot state (sitting/standing) is not yet known. Cannot move."

    def switch_mode(self, mode: str, object_name: Optional[str] = None) -> str:
        # time stamp
        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] Start switch mode time..")

        mode_requested = mode.strip().lower()
        msg_str = String()

        msg_str_mode = String()
        msg_str_mode.data = mode_requested

        try:
            if mode_requested == "keyboard":
                msg_str.data = "m"
                self.key_pressed_pub.publish(msg_str)
                self.switch_mode_pub.publish(msg_str_mode)
                response = "Switched to keyboard mode. Use keys w,a,s,d to move, t to stand, g to sit, and arrows to rotate and change altitude."

            elif mode_requested == "hand":
                msg_str.data = "h"
                self.key_pressed_pub.publish(msg_str)
                self.switch_mode_pub.publish(msg_str_mode)
                response = "Switched to hand gesture control mode."

            elif mode_requested == "tracking":
                if not object_name:
                    return "Error: To switch to tracking mode, you must specify an object_name."
                msg_str.data = "t"
                self.key_pressed_pub.publish(msg_str)
                # Immediately return the result from the helper function
                response = self.start_object_tracking(object_name)

            elif mode_requested == "stop tracking":
                msg_str.data = "s"  # stopping the tracking defaults to keyboard mode
                self.key_pressed_pub.publish(msg_str)
                # Immediately return the result from the helper function
                response = self.stop_object_tracking()

            else:
                response = f"Unsupported mode: '{mode}'. Valid modes are: keyboard, hand, tracking, stop tracking."

            # time stamp
            time_str_end = datetime.now().strftime("%H:%M:%S:%f")
            print(Fore.CYAN + f"[{time_str_end}] End switch mode time..")
            return response

        except Exception as e:
            return (
                f"Failed to switch mode for {self.robot_name} to '{mode_requested}' "
                f"(as '{msg_str.data}'): {e}"
            )

    def start_object_tracking(self, object_name: str) -> str:
        """
        Use this tool to start tracking a person holding a specific object. It will wait
        up to 5 seconds for a person holding this object to be detected. The robot MUST be  standing.

        First, you MUST choose the most similar object from this list of available options:
        [backpack, umbrella, handbag, bottle, cup, fork, knife, spoon, bowl, banana, apple, cell phone, book]
        Match the user's request to an object in the list. For example, if the user asks for a "phone", choose "cell phone".
        If you cannot find a clear match, respond by saying "There are no similar objects to track."
        :param object_name: str - The chosen object name from the list.


        Use this tool to start tracking a person holding a specific object. It will wait
        up to 5 seconds for a person holding this object to be detected. The robot MUST be  standing.

        First, you MUST choose the most similar object from this list of available options:
        [backpack, umbrella, handbag, bottle, cup, fork, knife, spoon, bowl, banana, apple, cell phone, book]
        Match the user's request to an object in the list. For example, if the user asks for a "phone", choose "cell phone".
        If you cannot find a clear match, respond by saying "There are no similar objects to track."
        :param object_name: str - The chosen object name from the list.
        """

        # time stamp
        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] Start start_tracking tool time..")

        if self.current_tracking_object:
            return f"Already tracking '{self.current_tracking_object}'. Please stop tracking first."

        # Reset the event and prepare for a new tracking task
        self.current_tracking_object = object_name
        self.tracking_confirmation_received.clear()

        self.get_logger().info(
            f"Attempting to track a person with a '{self.current_tracking_object}'. Searching for 5 seconds..."
        )

        success = self.tracking_confirmation_received.wait(timeout=5.0)

        if success:
            response = f"Successfully found and locked on to person with '{self.current_tracking_object}'."

            self.get_logger().info(response)

            time_str = time.strftime("%H:%M:%S")
            print(Fore.CYAN + f"[{time_str}] End tracking time..")

            return response
        else:
            self.current_tracking_object = None
            response = f"Failed to find a person with a '{object_name}' within 5 seconds. Please ensure they and the object are visible."
            self.get_logger().warn(response)

            time_str = datetime.now().strftime("%H:%M:%S:%f")
            print(Fore.CYAN + f"[{time_str}] End start_tracking tool time..")
            return response

    # Assuming tracking_info_pubs, ROBOT_NAME, and current_tracking_object are defined
    # in the global scope as in the original context.

    def stop_object_tracking(self) -> str:
        """
        Stops tracking the current object and clears the tracking target.
        An explicit "stop_tracking" message is sent to the tracking system.

        Stops tracking the current object and clears the tracking target.
        An explicit "stop_tracking" message is sent to the tracking system.
        """

        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] Start stop_tracking tool time..")

        try:
            stop_tracking_message = json.dumps(
                {"action": "stop_tracking", "params": {}}
            )
            self.tracking_signal_pub.publish(String(data=stop_tracking_message))
        except Exception as e:
            return f"Failed to publish stop tracking command for {self.robot_name}: {e}"
        previous_object = self.current_tracking_object
        self.current_tracking_object = None

        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] End stop_tracking tool time..")

        if previous_object:
            return f"{self.robot_name} has stopped tracking '{previous_object}'. Stop command was successfully published."
        else:
            return f"A stop command was sent to {self.robot_name} to ensure tracking is disabled."

    ############################################# Getters #########################################################################
    def get_prompts(self):
        prompts = RobotSystemPrompts(
            embodiment_and_persona="You are a robotic agent managing a robot dog. The robot dog you are operating is Boston dynamics' Spot",
            about_your_capabilities="You capabilities are limited to the available tools. Anything that is asked to you and not provided by a tool is beyond your capabilities",
            critical_instructions="Always use the corresponding tool if you can. If the user ask you to perform an action requiring to move the robot, always use the move tool."
            " Same for all other tools: if the user ask for an information/action requiring to use a tool, always use the relevant tool. "
            "Be concise and clear in your answers."
            "Produce short, clear sentences"
            "Do not repeat yourself.",
        )
        return prompts

    def get_tools(self):

        @tool
        def get_battery_status():
            """Provides detailed information about each battery installed in the robot.
            For instance, it includes :
            * the percentage of charge remaining,
            * the estimated remaining runtime,
            * the temperature readings.
            * a status indicator to flag battery health or errors.

            The status indicator is a number with the following meaning:
                - 0 -> STATUS UNKNOWN
                - 1 -> STATUS MISSING
                - 2 -> STATUS CHARGING
                - 3 -> STATUS DISCHARGING
                - 4 -> STATUS BOOTING
            Please make sure to communicate the meanings to the user, as they might not know what a raw number for the battery status mean.

            This should be called when necessary to guarantee accurate battery level information.
            """
            return self.get_battery_status()

        @tool
        def get_mobility_metrics():
            """
            Reports mobility statistics of the robot dog.
            The information that you can get through this tool include:
            * The total distance traveled by the robot,
            * The total time the robot has been moving,
            * The current physical posture of the robot, namely whether or not the robot dog is standing/sitting and the desired body position and orientation (pose) relative to the world.
            * The robot’s current motion configuration, namely whether or not the robot is currently moving, a locomotion behavior hint (e.g. walking, stair climbing), and whether the robot is actively in a stair-climbing mode.
            """
            return self.get_mobility_metrics()

        @tool
        def get_power_state():
            """
            Provides the current power supply conditions.
            The information that you can get through this tool include:
            * the state of the motor and shore power systems,
            * the charge level specific to locomotion systems,
            * the estimated runtime remaining for locomotion.
            * the accumulated electrical power usage.
            """
            return self.get_power_state()

        @tool
        def get_info_spot():
            """Gets the robot dog (spot) general information, such as its specie, version and nickname"""
            return self.get_info_spot()

        @tool
        def get_odometry():
            """Represents the robot's current estimated velocity, both linear and angular, in three dimensions."""
            return self.get_odometry()

        @tool
        def get_faults():
            """
            Gets faults reports of the robot dog. There are two faults types:
            * Behavior Fault State:
                Lists any active behavior-related faults.
            * System Fault State:
                Reports both active and historical faults detected in the robot’s internal systems.
            """
            return self.get_faults()

        @tool
        def get_wifi_connection_state():
            """Conveys the current Wi-Fi connection status of the robot.
            The information that you can get through this tool include:
            * the current operating mode of the wireless interface
            * the name (SSID) of the currently connected network if applicable
            The operating mode  is a number with the following meaning:
                - 0 -> MODE UNKNOWN
                - 1 -> MODE ACCESS POINT
                - 2 -> MODE CLIENT

            Please make sure to communicate the meanings (unknown, access point, client) to the user, as they might not know what a raw number  mean.

            """
            return self.get_wifi_connection_state()

        @tool
        def get_general_status():
            """Gets the current robot dog's latest reported state and general information.
            The status includes battery information, the robot's posture (standing, sitting, moving), wifi connection status, and the whether or not tracking is ongoing.
            You should use this tool if the user simply asks for the status of the robot.
            However, if they ask more details, please use the appropriate tools.
            For more detailed information, use the appropriate tools, namely
                * get_battery_status for battery information,
                * get_mobility_metrics for mobility metrics,
                * get_wifi_connection_state for the connection status
            """
            return self.get_general_status()

        @tool
        def sit():
            """Command the robot dog to sit and transition from a standing position (on 4 legs) to a sitting position.
            It cannot be used if the robot is already on the sitting. To know whether or not the robot is sitting, first get the status of the robot.
            """
            return self.sit()

        @tool
        def stand():
            """Command the robot to stand and transition from a sitting position to a standing position.
            It cannot be used if the robot is already standing.  To know whether or not the robot is sitting, first get the status of the robot.
            Do not attempt to stand the robot if the battery level is below 20% or if the robot is standing. In such cases, return an appropriate message.
            To have the battery level, use the get_battery_status() tool.
            """
            return self.stand()

        @tool
        def move(linear, angular, duration):
            """
            Move the robot with specified linear and angular velocities for a given duration.
            This function controls movement along three axes (x, y, z) and rotation.

            The coordinate system is as follows:
            - x-axis: +x is forward, -x is backward.
            - y-axis: +y is left, -y is right.
            - z-axis: +z is up, -z is down.
            - angular z-axis: +z is counter-clockwise turn (left), -z is clockwise turn (right).

            To perform this movement, the robot dog must be in the standing.
            The user may specify a speed (e.g., "velocity 1m/s", "go slowly"). If a speed is provided, use it to set the magnitude of the linear or angular velocity vector. If no speed is specified, use a default of 1 m/s or -1 m/s.
            If the user does not specify a time, assume a default duration of 1 second.

            :param linear: A list of 3 floats representing [x, y, z] velocity in m/s. This vector should be constructed based on the user's direction and specified speed.
                        For example, if the user says "go right at 1.2 m/s", the vector should be [0.0, -1.2, 0.0].
            :param angular: A float for z-axis angular velocity (rotation).
            :param duration: Duration of the movement in seconds.

            Do not attempt to move the robot if the battery level is below 20% or if the robot is sitting. In such cases, return an appropriate message.
            To have the battery level and whether or not the robot is sitting, you have the , use the get_general_status() tool.
            """
            return self.move(linear, angular, duration)

        @tool
        def switch_mode(mode, object_name):
            """
            Switches the control mode of the robot dog. Tell the user that he has to select the image window.
            The LLM should request modes like 'keyboard', 'hand', 'tracking' or 'stop tracking'.
            If the user selects 'keyboard', he has to know that to stand he has to use "t", to sit "g", to move the letters "a", "w", "d", "s". Still in keyboard mode
            the user must know that for rotation he/she can use "left-arrow" and "right-arrow" to move left or right respectively, and for altitude, he/she can use "up-arrow" to move up and "down-arrow" to move down.
            If the user selects 'hand', he has to know that he has to use the hands to control the robot dog, all the options are in the image window.
            If the user selects 'tracking', tracking': Start tracking a person holding a specific object.
            When using this mode, you must also provide the 'object_name' parameter.
            Choose the object from this list: [backpack, umbrella, handbag, bottle, cup, fork, knife, spoon, bowl, banana, apple, cell phone, book, laptop, keyboard].
            If the user selects 'stop tracking': Stop the current tracking task.

            :param mode: The desired control mode as a string (e.g., "keyboard", "hand", "tracking", "stop tracking").
            :param object_name: The name of the object to track. Required only for 'tracking' mode.
            """
            return self.switch_mode(mode, object_name)

        @tool
        def start_object_tracking(object_name):
            """
            Use this tool to start tracking a person holding a specific object. It will wait
            up to 5 seconds for a person holding this object to be detected. The robot MUST be  standing.

            First, you MUST choose the most similar object from this list of available options:
            [backpack, umbrella, handbag, bottle, cup, fork, knife, spoon, bowl, banana, apple, cell phone, book, laptop, keyboard]
            Match the user's request to an object in the list. For example, if the user asks for a "phone", choose "cell phone".
            If you cannot find a clear match, respond by saying "There are no similar objects to track."
            :param object_name: str - The chosen object name from the list.
            """
            return self.start_object_tracking(object_name)

        @tool
        def stop_object_tracking():
            """
            Stops tracking the current object and clears the tracking target.
            An explicit "stop_tracking" message is sent to the tracking system.
            """
            return self.stop_object_tracking()

        return [
            get_battery_status,
            get_mobility_metrics,
            get_info_spot,
            get_faults,
            get_odometry,
            get_general_status,
            get_power_state,
            stand,
            sit,
            move,
            switch_mode,
            start_object_tracking,
            stop_object_tracking,
            get_wifi_connection_state,
        ]
