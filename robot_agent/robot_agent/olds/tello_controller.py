import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from rosa import ROSA
from langchain.agents import tool
from std_msgs.msg import String, Empty, Float32
from geometry_msgs.msg import Twist
from plugin_base.plugin_base import PluginNode
from tello_msgs.msg import FlipControl, FlightStats
import asyncio
import time
import rclpy
from rclpy.node import Node
import threading
from rclpy.executors import MultiThreadedExecutor
from typing import List, Optional
from sensor_msgs.msg import BatteryState
from colorama import Fore, Style, init
import time
import json
from datetime import datetime
import logging

init(autoreset=True)

# Create a logger object named 'log'
log = logging.getLogger("InteractionLogger")
log.setLevel(logging.INFO)  # Set the minimum level of messages to record

# Create a file handler to write logs to a file named 'interaction_log.txt'
file_handler = logging.FileHandler("interaction_log.txt")

# Create a formatter to define the log message format (timestamp - level - message)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)

# Add the file handler to the logger
log.addHandler(file_handler)


from rclpy.publisher import Publisher


tracking_confirmation_received = threading.Event()
last_published_data = None

load_dotenv()  # This loads the variables from .env file

cmd_vel_pubs = {}
takeoff_pubs = {}
land_pubs = {}
flip_pubs = {}
tracking_info_pubs = {}
tracking_info_subs = {}
battery_levels = {}
battery_subs = {}
drone_states = {}
drone_state_subs = {}
mode_switch_pubs = {}
throw_takeoff_pubs = {}
palm_land_pubs = {}
current_tracking_object = None
FLY_MODE_STATE_MAP = {
    0: "ground",
    1: "air",
}

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
    67: "cell phone",
    73: "book",
}


class TelloController(Node):
    def __init__(self):
        super().__init__("tello_controller")
        self.warned_low_battery = False

        # Publishers
        vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        takeoff_pub = self.create_publisher(Empty, "/takeoff", 1)
        land_pub = self.create_publisher(Empty, "/land", 1)
        flip_pub = self.create_publisher(FlipControl, "/flip", 1)
        mode_switch_pub = self.create_publisher(String, "/key_pressed", 10)
        self.tracking_info_pub = self.create_publisher(String, "/tracking_signal", 10)
        # self.tracking_info_publisher_instance = self.create_publisher(String, '/tracking_signal', 10)
        throw_takeoff_pub = self.create_publisher(Empty, "/throw_and_go", 1)
        palm_land_pub = self.create_publisher(Empty, "/palm_land", 1)

        ### For interface tetsing
        self.llm_response_pub = self.create_publisher(String, "/llm_response", 1)
        self.user_query = None
        self.user_query_sub = self.create_subscription(
            String, "/user_query", self.user_query_callback, 10
        )
        ### End for interface testing

        # Subscribers
        battery_sub = self.create_subscription(
            BatteryState, "/battery_state", self.battery_callback, 10
        )
        self.drone_state_sub = self.create_subscription(
            FlightStats, "/flight_data", self.drone_state_callback, 10
        )
        self.tracking_info_subscription = self.create_subscription(
            String, "/tracking_info", self.tracking_info_callback, 10
        )
        self.tracking_signal_subscriber = self.create_subscription(
            String, "/tracking_signal", self.tracking_signal_print_callback, 10
        )

        # Register with global maps
        add_cmd_vel_pub(ROBOT_NAME, vel_pub)
        add_takeoff_pub(ROBOT_NAME, takeoff_pub)
        add_land_pub(ROBOT_NAME, land_pub)
        add_flip_pub(ROBOT_NAME, flip_pub)
        add_tracking_info_pub(ROBOT_NAME, self.tracking_info_pub)
        add_battery_sub(ROBOT_NAME, battery_sub)
        add_mode_switch_pub(ROBOT_NAME, mode_switch_pub)
        add_drone_state_sub(ROBOT_NAME, self.drone_state_sub)
        add_throw_takeoff_pub(ROBOT_NAME, throw_takeoff_pub)
        add_palm_land_pub(ROBOT_NAME, palm_land_pub)

    def tracking_signal_print_callback(self, msg: String):
        self.get_logger().info("--- FINAL TRACKING SIGNAL (Output) ---")
        self.get_logger().info(f"{msg.data}")
        self.get_logger().info("------------------------------------")

    def battery_callback(self, msg: BatteryState):
        if msg.percentage is not None:
            percent_0_to_100 = msg.percentage
            update_battery_level(ROBOT_NAME, percent_0_to_100)

            if 10.0 <= percent_0_to_100 < 20.0 and not self.warned_low_battery:
                self.warned_low_battery = True
                self.get_logger().warn(
                    f"Battery for {ROBOT_NAME} is at {percent_0_to_100:.1f}%. "
                    "Consider landing soon."
                )
            elif percent_0_to_100 >= 20.0:
                self.warned_low_battery = False

    def user_query_callback(self, msg: String):
        self.user_query = msg.data

    def tracking_info_callback(self, msg: String):
        """
        This callback finds a person who is associated with the target object,
        publishes their data ONCE to /tracking_signal, and then stops until a new command.
        """
        global current_tracking_object, tracking_confirmation_received, last_published_data

        # 1. If we are not actively looking for an object, do nothing.
        if not current_tracking_object:
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
                    if current_tracking_object in held_objects:

                        # 4. We found the compatible person! Publish their complete data.
                        self.get_logger().info(
                            f"MATCH FOUND: Sending compatible person (ID: {person_data.get('id')}) to /tracking_signal."
                        )

                        filtered_info = json.dumps(person_data)
                        self.tracking_info_pub.publish(String(data=filtered_info))

                        last_published_data = filtered_info
                        tracking_confirmation_received.set()
                        current_tracking_object = None

                        break  # Stop checking other people in this message

        except Exception as e:
            self.get_logger().error(f"Error in tracking_info_callback: {e}")

    def drone_state_callback(self, msg: FlightStats):
        current_state_data = {
            "em_sky": msg.em_sky,
            "fly_mode": msg.fly_mode,
            "height": msg.height,
            "physical_state": FLY_MODE_STATE_MAP.get(msg.em_sky, "unknown"),
            "wifi_strength": msg.wifi_strength,
        }
        drone_states[ROBOT_NAME] = current_state_data


ROBOT_NAME = "tello"


def add_cmd_vel_pub(name: str, publisher: Publisher):
    cmd_vel_pubs[name] = publisher


def remove_cmd_vel_pub(name: str):
    cmd_vel_pubs.pop(name, None)


def add_takeoff_pub(name: str, publisher: Publisher):
    takeoff_pubs[name] = publisher


def remove_takeoff_pub(name: str):
    takeoff_pubs.pop(name, None)


def add_land_pub(name: str, publisher: Publisher):
    land_pubs[name] = publisher


def remove_land_pub(name: str):
    land_pubs.pop(name, None)


def add_flip_pub(name: str, publisher: Publisher):
    flip_pubs[name] = publisher


def remove_flip_pub(name: str):
    flip_pubs.pop(name, None)


def add_tracking_info_pub(name: str, publisher: Publisher):
    tracking_info_pubs[name] = publisher


def remove_tracking_info_pub(name: str):
    tracking_info_pubs.pop(name, None)


def update_battery_level(name: str, level: float):
    battery_levels[name] = level


def add_battery_sub(name: str, subscription):
    battery_subs[name] = subscription


def remove_battery_sub(name: str):
    battery_subs.pop(name, None)


def add_drone_state_sub(name: str, subscription):
    drone_state_subs[name] = subscription


def remove_drone_state_sub(name: str):
    drone_state_subs.pop(name, None)


def add_mode_switch_pub(name: str, publisher: Publisher):
    mode_switch_pubs[name] = publisher


def remove_mode_switch_pub(name: str):
    mode_switch_pubs.pop(name, None)


def add_throw_takeoff_pub(name: str, publisher: Publisher):
    throw_takeoff_pubs[name] = publisher


def remove_throw_takeoff_pub(name: str):
    throw_takeoff_pubs.pop(name, None)


def add_palm_land_pub(name: str, publisher: Publisher):
    palm_land_pubs[name] = publisher


def remove_palm_land_pub(name: str):
    palm_land_pubs.pop(name, None)


openai_llm = ChatOpenAI(
    model="gpt-4-turbo",  # or your preferred model
    temperature=0,
    timeout=None,
    max_retries=2,
)


ollamallm = ChatOllama(
    model="llama3.2",
    temperature=0,
    base_url="http://10.42.0.1:11434",
    system_message=(
        "You are a ROS-enabled assistant. When the user asks for a command like 'take off', "
        "use the corresponding tool like `takeoff()`. Do not explain; just act using the tools provided."
        "If the user asks about the tools, tell him all the available tools and their descriptions. "
    ),
)


@tool
def takeoff() -> str:
    """Command the robot to take off and transition from ground to air. It cannot be used if the robot is already in the air."""

    # time stamp
    time_str = datetime.now().strftime("%H:%M:%S:%f")
    print(Fore.CYAN + f"[{time_str}] Start takeoff tool time..")

    pub = takeoff_pubs.get(ROBOT_NAME)
    state_data = drone_states.get(ROBOT_NAME)
    if not pub:
        return f"No takeoff publisher found for {ROBOT_NAME}"
    current_physical_state = "unknown"
    if state_data and "physical_state" in state_data:
        current_physical_state = state_data["physical_state"]
    if current_physical_state != "ground":
        if state_data is None:
            return f"Drone state for {ROBOT_NAME} is not yet known. Cannot takeoff."
        return f"{ROBOT_NAME} is not on the ground. Current state: '{current_physical_state}'. Cannot takeoff."
    try:
        pub.publish(Empty())

        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] End takeoff tool time..")

        return f"{ROBOT_NAME} is taking off."
    except Exception as e:
        return f"Failed to take off {ROBOT_NAME}: {e}"


@tool
def move(linear: List[float], angular: float, duration: int) -> str:
    """
    Move the robot with specified linear and angular velocities for a given duration.
    This function controls movement along three axes (x, y, z) and rotation.

    The coordinate system is as follows:
    - x-axis: +x is forward, -x is backward.
    - y-axis: +y is left, -y is right.
    - z-axis: +z is up, -z is down.
    - angular z-axis: +z is counter-clockwise turn (left), -z is clockwise turn (right).

    To perform this movement, the drone must be in the air.
    The user may specify a speed (e.g., "velocity 1m/s", "go slowly"). If a speed is provided, use it to set the magnitude of the linear velocity vector. If no speed is specified, use a default of 1 m/s or -1 m/s.
    If the user does not specify a time, assume a default duration of 1 second.
    If the drone's height is below 8 units (8dm), it cannot move down.

    :param linear: A list of 3 floats representing [x, y, z] velocity in m/s. This vector should be constructed based on the user's direction and specified speed.
                   For example, if the user says "go right at 1.2 m/s", the vector should be [0.0, -1.2, 0.0].
    :param angular: A float for z-axis angular velocity (rotation).
    :param duration: Duration of the movement in seconds.
    """

    # time stamp
    time_str = datetime.now().strftime("%H:%M:%S:%f")
    print(Fore.CYAN + f"[{time_str}] Start motion time..")

    pub = cmd_vel_pubs.get(ROBOT_NAME)
    state_data = drone_states.get(ROBOT_NAME)
    if not pub:
        return f"No cmd_vel publisher found for {ROBOT_NAME}"

    # (All of your safety checks for state, height, etc. are correct and remain here)
    if not state_data:
        return f"Drone state for {ROBOT_NAME} is not yet known. Cannot move."
    current_physical_state = state_data.get("physical_state")
    current_height = state_data.get("height")
    if current_physical_state != "air":
        return f"{ROBOT_NAME} is not in the air. Current state: '{current_physical_state}'. Cannot move."
    if current_height is not None and current_height < 8 and linear[2] < 0:
        return f"{ROBOT_NAME} is too low (height: {current_height} dm) to move further down. Height must be at least 8 dm."

    try:
        msg_twist = Twist()
        msg_twist.linear.x, msg_twist.linear.y, msg_twist.linear.z = linear
        msg_twist.angular.z = angular

        # This loop correctly handles the drone's safety watchdog
        rate = 30
        sleep_interval = 1.0 / rate
        start_time = time.time()

        print(
            f"DEBUG: LLM called move() with linear={linear}, angular={angular}, duration={duration}s"
        )

        while time.time() - start_time < duration:
            pub.publish(msg_twist)
            time.sleep(sleep_interval)

        # Send a final command to stop the drone
        pub.publish(Twist())

        # time stamp
        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] End motion time..")

        return f"Moved {ROBOT_NAME} with linear={linear}, angular={angular} for {duration}s and then stopped."
    except Exception as e:
        return f"Failed to move {ROBOT_NAME}: {e}"


@tool
def land() -> str:
    """Command the robot to land and transition from air to ground. It cannot be used if the robot is already on the ground."""

    # time stamp
    time_str = datetime.now().strftime("%H:%M:%S:%f")
    print(Fore.CYAN + f"[{time_str}] Start landing time..")

    pub = land_pubs.get(ROBOT_NAME)
    state_data = drone_states.get(ROBOT_NAME)
    if not pub:
        return f"No land publisher found for {ROBOT_NAME}"
    current_physical_state = "unknown"
    if state_data and "physical_state" in state_data:
        current_physical_state = state_data["physical_state"]
    if current_physical_state != "air":
        if current_physical_state == "ground":
            return f"{ROBOT_NAME} is already on the ground. Current state: '{current_physical_state}'. Cannot land."
        elif state_data is None:
            return f"Drone state for {ROBOT_NAME} is not yet known. Cannot land."
        return f"{ROBOT_NAME} is not in the air. Current state: '{current_physical_state}'. Cannot land."
    try:
        pub.publish(Empty())

        # time stamp
        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] End landing time..")

        return f"{ROBOT_NAME} is landing."
    except Exception as e:
        return f"Failed to land {ROBOT_NAME}: {e}"


@tool
def flip(direction: str) -> str:
    """Command the drone to perform a flip in the specified direction. If the direction is not provided, by default, forward. Valid directions: 'forward', 'backward', 'left', 'right'.
    To perform this movement the drone must be in the air (em_sky=1), at a height of at least 8 units (e.g. 8dm), and in fly_mode 6 or 31.
    The battery level must be above 20% to perform the flip maneuver.
    If in air but not in fly_mode 6 or 31, it will wait up to 10 seconds for the mode to change.
    """

    # time stamp
    time_str = datetime.now().strftime("%H:%M:%S:%f")
    print(Fore.CYAN + f"[{time_str}] Start flip time..")

    state_data = drone_states.get(ROBOT_NAME)
    battery_level = battery_levels.get(ROBOT_NAME)

    if not state_data:
        return f"Drone state for {ROBOT_NAME} is not yet known. Cannot flip."
    current_physical_state = state_data.get("physical_state")
    current_height = state_data.get("height")
    current_fly_mode = state_data.get("fly_mode")
    current_em_sky = state_data.get("em_sky")

    if current_physical_state != "air":
        return f"{ROBOT_NAME} is not in the air. Current state: '{current_physical_state}'. Cannot flip."

    if current_height is None:
        return f"Drone height for {ROBOT_NAME} is unknown. Cannot flip."
    if current_height < 8:
        return f"{ROBOT_NAME} is too low (height: {current_height} dm). Height must be at least 8 dm to flip."

    if battery_level is None:
        return "Battery level is unknown. Cannot perform flip."
    if battery_level < 20.0:
        return f"Battery too low ({battery_level:.2f}%). Flip maneuver is disabled. (Requires >20%)"

    pub = flip_pubs.get(ROBOT_NAME)
    if not pub:
        return f"No flip publisher found for {ROBOT_NAME}"
    if current_em_sky == 1 and (current_fly_mode == 6 or current_fly_mode == 31):
        pass
    elif current_em_sky == 1:
        print(
            f"INFO: {ROBOT_NAME} is in air but fly_mode is {current_fly_mode}. Waiting up to 10s for fly_mode 6 or 31..."
        )
        start_time = time.time()
        while time.time() - start_time < 10:
            state_data_updated = drone_states.get(ROBOT_NAME)
            if state_data_updated:
                current_fly_mode = state_data_updated.get("fly_mode")
                current_em_sky_updated = state_data_updated.get("em_sky")
                current_height_updated = state_data_updated.get("height")
                current_physical_state_updated = state_data_updated.get(
                    "physical_state"
                )

                if current_physical_state_updated != "air":
                    return f"{ROBOT_NAME} is no longer in the air (state: {current_physical_state_updated}). Aborting flip."
                if current_height_updated is None or current_height_updated < 8:
                    return f"{ROBOT_NAME} became too low (height: {current_height_updated} dm). Aborting flip."

                if current_fly_mode == 6 or current_fly_mode == 31:
                    print(
                        f"INFO: {ROBOT_NAME} fly_mode changed to {current_fly_mode}. Proceeding with flip."
                    )
                    break

            time.sleep(0.5)
        else:
            return (
                f"{ROBOT_NAME} did not enter fly_mode 6 or 31 within 10 seconds "
                f"(current mode: {current_fly_mode}, height: {current_height}, em_sky: {current_em_sky}). Flip command cancelled."
            )
    else:
        return (
            f"Cannot flip. Drone is not in a valid state for flip preconditions "
            f"(em_sky: {current_em_sky}, fly_mode: {current_fly_mode}, height: {current_height})."
        )

    try:
        msg_flip = FlipControl()
        valid_directions = ["forward", "backward", "left", "right"]
        direction_lower = direction.lower()
        if direction_lower not in valid_directions:
            return f"Invalid flip direction: {direction}. Valid are: {', '.join(valid_directions)}"

        if direction_lower == "left":
            msg_flip.flip_left = True
        elif direction_lower == "right":
            msg_flip.flip_right = True
        elif direction_lower == "forward":
            msg_flip.flip_forward = True
        elif direction_lower == "backward":
            msg_flip.flip_backward = True

        pub.publish(msg_flip)

        # time stamp
        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] End flip time..")

        return f"{ROBOT_NAME} performed a flip to the {direction}."
    except Exception as e:
        return f"Failed to flip {ROBOT_NAME}: {e}"


@tool
def get_battery_level() -> str:
    """Gets the current battery level of the robot."""
    level = battery_levels.get(ROBOT_NAME)
    if level is not None:
        return f"The battery level for {ROBOT_NAME} is currently {level:.2f}%."
    else:
        return f"Battery level for {ROBOT_NAME} has not been reported yet or is unavailable."


@tool
def status_drone() -> str:
    """Gets the current drone physical state (air/ground), battery level, height, fly_mode, and the wifi strength."""
    state_data = drone_states.get(ROBOT_NAME)
    level = battery_levels.get(ROBOT_NAME)
    state_str = "unknown"
    height_str = "unknown"
    fly_mode_str = "unknown"
    wifi_strength_str = "unknown"
    if state_data:
        state_str = state_data.get("physical_state", "unknown")
        height_val = state_data.get("height")
        height_str = f"{height_val} dm" if height_val is not None else "unknown"
        fly_mode_val = state_data.get("fly_mode")
        fly_mode_str = str(fly_mode_val) if fly_mode_val is not None else "unknown"
        wifi_strength_val = state_data.get("wifi_strength")
        wifi_strength_str = (
            f"{wifi_strength_val}/100" if wifi_strength_val is not None else "unknown"
        )
    battery_str = f"{level:.2f}%" if level is not None else "unknown"
    tracking_info_str = (
        f" Actively tracking: '{current_tracking_object}'."
        if current_tracking_object
        else " Not currently tracking."
    )
    return (
        f"Drone {ROBOT_NAME} status: Physical State='{state_str}', Height='{height_str}', "
        f"FlyMode='{fly_mode_str}', Battery='{battery_str}', WiFi Strength='{wifi_strength_str}'.{tracking_info_str}"
    )


@tool
def switch_mode(mode: str, object_name: Optional[str] = None) -> str:
    """
    Switches the control mode of the drone. Tell the user that he has to select the image window.
    The LLM should request modes like 'keyboard', 'hand', 'tracking' or 'stop tracking'.
    If the user selects 'keyboard', he has to know that to takeoff he has to use "t", to land "l", to move the letters "a", "w", "d", "s".
    If the user selects 'hand', he has to know that he has to use the hands to control the drone, all the options are in the image window.
    If the user selects 'tracking', tracking': Start tracking a person holding a specific object.
    When using this mode, you must also provide the 'object_name' parameter.
    Choose the object from this list: [backpack, umbrella, handbag, bottle, cup, fork, knife, spoon, bowl, banana, apple, cell phone, book].
    If the user selects 'stop tracking': Stop the current tracking task.

    :param mode: The desired control mode as a string (e.g., "keyboard", "hand", "tracking", "stop tracking").
    :param object_name: The name of the object to track. Required only for 'tracking' mode.
    """
    # time stamp
    time_str = datetime.now().strftime("%H:%M:%S:%f")
    print(Fore.CYAN + f"[{time_str}] Start switch mode time..")

    pub = mode_switch_pubs.get(ROBOT_NAME)
    if not pub:
        return f"No mode_switch publisher found for {ROBOT_NAME}."

    mode_requested = mode.strip().lower()
    msg_str = String()

    try:
        if mode_requested == "keyboard":
            msg_str.data = "m"
            pub.publish(msg_str)
            response = "Switched to keyboard mode. Use keys w,a,s,d to move, t to takeoff, l to land."

        elif mode_requested == "hand":
            msg_str.data = "h"
            pub.publish(msg_str)
            response = "Switched to hand gesture control mode."

        elif mode_requested == "tracking":
            if not object_name:
                return "Error: To switch to tracking mode, you must specify an object_name."
            msg_str.data = "t"
            pub.publish(msg_str)
            # Immediately return the result from the helper function
            response = start_object_tracking(object_name)

        elif mode_requested == "stop tracking":
            msg_str.data = "s"
            pub.publish(msg_str)
            # Immediately return the result from the helper function
            response = stop_object_tracking()

        else:
            response = f"Unsupported mode: '{mode}'. Valid modes are: keyboard, hand, tracking, stop tracking."

        # time stamp
        time_str_end = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str_end}] End switch mode time..")
        return response

    except Exception as e:
        return (
            f"Failed to switch mode for {ROBOT_NAME} to '{mode_requested}' "
            f"(as '{msg_str.data}'): {e}"
        )


def start_object_tracking(object_name: str) -> str:
    """
    Use this tool to start tracking a person holding a specific object. It will wait
    up to 5 seconds for a person holding this object to be detected. The drone MUST be in the air.

    First, you MUST choose the most similar object from this list of available options:
    [backpack, umbrella, handbag, bottle, cup, fork, knife, spoon, bowl, banana, apple, cell phone, book]
    Match the user's request to an object in the list. For example, if the user asks for a "phone", choose "cell phone".
    If you cannot find a clear match, respond by saying "There are no similar objects to track."
    :param object_name: str - The chosen object name from the list.
    """

    # time stamp
    time_str = datetime.now().strftime("%H:%M:%S:%f")
    print(Fore.CYAN + f"[{time_str}] Start start_tracking tool time..")

    global current_tracking_object, tracking_confirmation_received, last_published_data

    if current_tracking_object:
        return (
            f"Already tracking '{current_tracking_object}'. Please stop tracking first."
        )

    # Reset the event and prepare for a new tracking task
    tracking_confirmation_received.clear()
    last_published_data = None
    current_tracking_object = object_name

    node = globals().get("node")
    if node:
        node.get_logger().info(
            f"Attempting to track a person with a '{current_tracking_object}'. Searching for 5 seconds..."
        )

    success = tracking_confirmation_received.wait(timeout=5.0)

    if success:
        response = f"Successfully found and locked on to person with '{current_tracking_object}'. Published data: {last_published_data}"
        if node:
            node.get_logger().info(response)

        time_str = time.strftime("%H:%M:%S")
        print(Fore.CYAN + f"[{time_str}] End tracking time..")

        return response
    else:
        current_tracking_object = None
        response = f"Failed to find a person with a '{object_name}' within 5 seconds. Please ensure they and the object are visible."
        if node:
            node.get_logger().warn(response)

        time_str = datetime.now().strftime("%H:%M:%S:%f")
        print(Fore.CYAN + f"[{time_str}] End start_tracking tool time..")
        return response


import json
from std_msgs.msg import String

# Assuming tracking_info_pubs, ROBOT_NAME, and current_tracking_object are defined
# in the global scope as in the original context.


def stop_object_tracking() -> str:
    """
    Stops tracking the current object and clears the tracking target.
    An explicit "stop_tracking" message is sent to the tracking system.
    """

    time_str = datetime.now().strftime("%H:%M:%S:%f")
    print(Fore.CYAN + f"[{time_str}] Start stop_tracking tool time..")

    global current_tracking_object

    # Get the publisher for the tracking topic.
    pub = tracking_info_pubs.get(ROBOT_NAME)
    if not pub:
        return f"Error: No tracking_info publisher found for {ROBOT_NAME}."

    try:
        stop_tracking_message = json.dumps({"action": "stop_tracking", "params": {}})
        pub.publish(String(data=stop_tracking_message))
    except Exception as e:
        return f"Failed to publish stop tracking command for {ROBOT_NAME}: {e}"
    previous_object = current_tracking_object
    current_tracking_object = None

    time_str = datetime.now().strftime("%H:%M:%S:%f")
    print(Fore.CYAN + f"[{time_str}] End stop_tracking tool time..")

    if previous_object:
        return f"{ROBOT_NAME} has stopped tracking '{previous_object}'. Stop command was successfully published."
    else:
        return (
            f"A stop command was sent to {ROBOT_NAME} to ensure tracking is disabled."
        )


@tool
def palm_land() -> str:
    """Command the robot to land on an open palm. The drone must be in the air and will descend to land on a detected hand when one is presented below it."""
    pub = palm_land_pubs.get(ROBOT_NAME)
    state_data = drone_states.get(ROBOT_NAME)
    if not pub:
        return f"No palm_land publisher found for {ROBOT_NAME}"
    current_physical_state = "unknown"
    if state_data:
        current_physical_state = state_data.get("physical_state", "unknown")

    if current_physical_state != "air":
        if current_physical_state == "ground":
            return f"{ROBOT_NAME} is already on the ground. Cannot palm land."
        elif state_data is None:
            return f"Drone state for {ROBOT_NAME} is not yet known. Cannot palm land."
        return f"{ROBOT_NAME} is not in the air. Current state: '{current_physical_state}'. Cannot palm land."  # MODIFIED: Message improved
    try:
        pub.publish(Empty())
        return f"{ROBOT_NAME} is initiating palm landing. Please position your open palm beneath the drone."
    except Exception as e:
        return f"Failed to initiate palm land for {ROBOT_NAME}: {e}"


@tool
def throw_and_go() -> str:
    """Command the robot to perform a throw takeoff. The drone must be on the hands of the user
        and then physically thrown within a 5-secon
    export function VideoContd arming window to initiate flight."""  # MODIFIED: Docstring updated to reflect arming window.

    pub = throw_takeoff_pubs.get(ROBOT_NAME)
    state_data = drone_states.get(ROBOT_NAME)
    if not pub:
        return f"No throw_takeoff publisher found for {ROBOT_NAME}"
    current_physical_state = "unknown"
    if state_data:
        current_physical_state = state_data.get("physical_state", "unknown")

    if current_physical_state != "ground":
        if state_data is None:
            return f"Drone state for {ROBOT_NAME} is not yet known. Cannot perform throw and go."
        return f"{ROBOT_NAME} is not on the ground. Current state: '{current_physical_state}'. Cannot perform throw and go."
    try:
        arming_duration_seconds = 5
        publish_frequency_hz = 10
        sleep_interval = 1.0 / publish_frequency_hz
        start_time = time.time()
        while (time.time() - start_time) < arming_duration_seconds:
            pub.publish(Empty())
            time.sleep(sleep_interval)
        return f"{ROBOT_NAME} arming window for throw and go ({arming_duration_seconds}s) has ended. If thrown, drone should react."
    except Exception as e:
        return f"Failed during throw and go sequence for {ROBOT_NAME}: {e}"


tools = [
    move,
    takeoff,
    land,
    flip,
    get_battery_level,
    status_drone,
    switch_mode,
    throw_and_go,
    palm_land,
]

# Pass the LLM to ROSA
rosa = ROSA(ros_version=2, llm=openai_llm, streaming=True, tools=tools)


def print_response(query: str):
    response = rosa.invoke(query)
    # ... code to display response ...


async def submit(query: str):
    return await stream_response(query)


async def stream_response(query: str):
    print(Fore.BLUE + Style.BRIGHT + f"\n👤 User: {query}\n")

    response = ""

    async for event in rosa.astream(query):
        if event["type"] == "token":
            print(Fore.GREEN + event["content"], end="", flush=True)
            response = response + event["content"]
        elif event["type"] == "tool_start":
            print(Fore.YELLOW + f"\n🛠️ Starting tool: {event['name']}")
        elif event["type"] == "tool_end":
            print(Fore.YELLOW + f"\n✅ Finished tool: {event['name']}")
            await asyncio.sleep(1)
        elif event["type"] == "final":
            pass
            # print(Fore.CYAN + Style.BRIGHT + f"\n📤 Final output: {event['content']}")
        elif event["type"] == "error":
            print(Fore.RED + f"\n❌ Error: {event['content']}")

    return response


# Function to run the ROSA agent
async def run(node):
    # Print the time when the session starts
    start_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
    print(
        Fore.CYAN + Style.BRIGHT + f"\n--- ROSA Session Started at {start_time_str} ---"
    )

    query = None

    while True:

        # Get the user's command

        # query = node.user_query

        # --- 1. Print the time BEFORE the prompt ---
        prompt_time_str = time.strftime("%H:%M:%S")
        # The '\n' adds a space before the new prompt, 'end=""' keeps the cursor on the same line
        print(Fore.CYAN + f"\n[{prompt_time_str}] ", end="")

        query = input("Enter your prompt (or 'exit' to quit): ")

        if query.lower() == "exit":
            log.info("--- Session Ended ---")
            break

        # Log the prompt to the file
        log.info(f"USER_PROMPT: {query}")

        # Start processing the command
        processing_time_str = time.strftime("%H:%M:%S")
        print(Fore.CYAN + f"[{processing_time_str}] Processing command...")

        responseMsg = String()
        responseMsg.data = await submit(query)
        node.llm_response_pub.publish(responseMsg)

        processing_time_str = time.strftime("%H:%M:%S")
        print(Fore.CYAN + f"[{processing_time_str}] Response received...")


# asyncio.run(run())


# ROS init and run
def main(args=None):
    rclpy.init(args=args)
    node = TelloController()

    # Use executor in a separate thread
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    def spin():
        executor.spin()

    # Start the ROS spinning in a background thread
    spin_thread = threading.Thread(target=spin, daemon=True)
    spin_thread.start()

    try:
        asyncio.run(run(node))
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
