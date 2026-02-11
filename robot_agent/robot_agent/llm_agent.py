import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from rosa import ROSA

from langchain_community.chat_message_histories import ChatMessageHistory
from std_msgs.msg import String
from std_srvs.srv import Trigger
from langchain.tools import tool

import rclpy
from rclpy.node import Node

from rclpy.executors import MultiThreadedExecutor

import asyncio
import time
import threading


from colorama import Fore, Style, init
import logging

from robot_agent.spot_controller import SpotController
from robot_agent.tello_controller import TelloController

from robot_agent.voice_input_output import VoiceInOut

from robot_agent.text_input import TextInput


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


load_dotenv()  # This loads the variables from .env file


class Agent(Node):

    llm_model_name = "gpt-3.5-turbo"  # "gpt-4"
    user_query_topic = "/user_query"
    llm_response_topic = "/llm_response"
    change_robot_topic = "/change_robot_name"

    def __init__(self, robot_node: Node, robot_name: str, voice_node: Node = None):
        super().__init__("RoboticAgent")

        self.llm_model = None
        self._init_model()

        self.llm_response_pub = None
        self.user_query_sub = None
        self.change_robot_sub = None

        self.robots = dict()

        self.rosa = None

        self.chat_history = ChatMessageHistory(messages=[])

        self.current_robot_name = None

        self.event_loop = asyncio.new_event_loop()

        self.event_loop_thread = threading.Thread(
            target=self.event_loop.run_forever, daemon=True
        )
        self.event_loop_thread.start()

        self.add_robot(robot_node, robot_name)
        # to set the current robot, make sure that the llm model was already initialized
        self.set_current_robot(robot_name)

        self.voice_node = voice_node

        self.stop_tts_srv = self.create_service(
            Trigger, "/stop_tts_srv", self.stop_tts_callback
        )

        # Print the time when the session starts
        start_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
        print(
            Fore.CYAN
            + Style.BRIGHT
            + f"\n--- ROSA Session Started at {start_time_str} ---"
        )

        self._init_parameters()
        self._init_publishers()
        self._init_subscriptions()

    ########################################## Initialization Methods ############################################################################

    def _init_parameters(self) -> None:
        """Method to initialize parameters such as ROS topics' names"""
        self.declare_parameter("llm_model_name", self.llm_model_name)
        self.declare_parameter("user_query_topic", self.user_query_topic)
        self.declare_parameter("llm_response_topic", self.llm_response_topic)
        self.declare_parameter("change_robot_topic", self.change_robot_topic)

        self.llm_model_name = (
            self.get_parameter("llm_model_name").get_parameter_value().string_value
        )

        self.user_query_topic = (
            self.get_parameter("user_query_topic").get_parameter_value().string_value
        )

        self.llm_response_topic = (
            self.get_parameter("llm_response_topic").get_parameter_value().string_value
        )
        self.change_robot_topic = (
            self.get_parameter("change_robot_topic").get_parameter_value().string_value
        )

    def _init_publishers(self) -> None:
        """Method to initialize publishers"""
        self.llm_response_pub = self.create_publisher(
            String, self.llm_response_topic, 10
        )

    def _init_subscriptions(self) -> None:
        """Method to initialize subscriptions"""

        self.user_query_sub = self.create_subscription(
            String, self.user_query_topic, self.user_query_callback, 10
        )
        self.change_robot_sub = self.create_subscription(
            String, self.change_robot_topic, self.change_robot_callback, 10
        )

    def _init_model(self) -> None:
        """Method to initialize the LLM model"""

        if self.llm_model_name == "gpt-4":

            self.llm_model = ChatOpenAI(
                model="gpt-4",
                temperature=0,
                timeout=None,
                max_retries=2,
            )
        elif self.llm_model_name == "gpt-4-turbo":
            self.llm_model = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0,
                timeout=None,
                max_retries=2,
            )
        elif self.llm_model_name == "gpt-3.5-turbo":
            self.llm_model = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                timeout=None,
                max_retries=2,
            )
        elif self.llm_model_name == "llama3.2":
            self.llm_model = ChatOllama(
                model="llama3.2",
                temperature=0,
                base_url="http://10.42.0.1:11434",
                system_message=(
                    "You are a ROS-enabled assistant. When the user asks for a command like 'take off', "
                    "use the corresponding tool like `takeoff()`. Do not explain; just act using the tools provided."
                    "If the user asks about the tools, tell him all the available tools and their descriptions. "
                ),
            )
        else:
            self.get_logger().warning(
                f"No specific model name provided or model not recognized.\nDefaulting to gpt-3.5-turbo."
            )
            # Default to using gpt-3.5-turbo if no model name is provided
            self.llm_model = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                timeout=None,
                max_retries=2,
            )

    def add_robot(self, node: Node, robot_name: str):

        if robot_name not in self.robots:
            robot_dict = dict()
            robot_dict["robot_tools"] = node.get_tools()
            robot_dict["robot_prompts"] = node.get_prompts()
            self.robots[robot_name] = robot_dict
        else:

            self.get_logger().warn(
                f"Robot already exists in our dictionnary: {self.robots}"
            )

    def remove_robot(self, robot_name):
        if robot_name in self.robots:
            self.robots.pop(robot_name)

            if self.current_robot_name == robot_name:
                self.current_robot_name = None
                self.rosa = None

        else:
            self.get_logger().warn(
                f"Robot doesn't exist in our dictionnary: {self.robots}"
            )

    def set_current_robot(self, robot_name):
        if robot_name in self.robots:
            self.current_robot_name = robot_name
            self.rosa = ROSA(
                ros_version=2,
                llm=self.llm_model,
                streaming=True,
                tools=self.robots[robot_name]["robot_tools"],
                prompts=self.robots[robot_name]["robot_prompts"],
            )

        else:
            self.get_logger().warn(
                f"Robot {robot_name} doesn't exist. Make sure to add {robot_name} first."
            )

    ########################################## Subscriber callback ############################################################################
    def user_query_callback(self, msg) -> None:
        """Callback for the subscriber node (to topic self.user_query_topic).
        Receives user query messages."""
        self.user_query = msg.data
        self.chat_history.add_user_message(self.user_query)

        if self.current_robot_name:
            asyncio.run_coroutine_threadsafe(self.send_query(msg.data), self.event_loop)

        else:
            self.get_logger().debug(
                "Got a query, but the current agent is not yet initialized"
            )

    def change_robot_callback(self, msg) -> None:
        """Callback for the subscriber node (to topic self.change_robot_topic).
        Receives the name of the robot to switch to."""
        new_robot_name = msg.data.strip()
        if new_robot_name != self.current_robot_name:
            if new_robot_name in self.robots:
                self.set_current_robot(new_robot_name)
                self.get_logger().debug(f"Switched to robot: {new_robot_name}")
            else:
                self.get_logger().warn(
                    f"Robot '{new_robot_name}' not found. Available robots: {list(self.robots.keys())}"
                )
        else:
            self.get_logger().info(f"Already using robot: {new_robot_name}")

    def stop_tts_callback(self, request, response):
        """Callback method to stop Piper TTS when requested via service"""
        # Set the flag to False to stop Piper TTS
        try:
            if self.voice_node is not None:
                self.voice_node.stop_tts = True
                self.get_logger().debug("stop_tts set to True")
                response.success = True
                return response
            else:
                raise Exception("Voice node is not initialized.")
        except Exception as e:
            self.get_logger().error(f"An error occurred while trying to stop TTS: {e}")
            response.success = False
            return response

    ########################################## Query handling ############################################################################
    async def get_response(self, query: str):
        print(Fore.BLUE + Style.BRIGHT + f"\n👤 User: {query}\n")

        response = ""

        async for event in self.rosa.astream(query):
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

    async def send_query(self, query):

        # Get the user's command

        # --- 1. Print the time BEFORE the prompt ---
        prompt_time_str = time.strftime("%H:%M:%S")
        # The '\n' adds a space before the new prompt, 'end=""' keeps the cursor on the same line
        print(Fore.CYAN + f"\n[{prompt_time_str}] ", end="")

        # query = input("Enter your prompt (or 'exit' to quit): ")

        # Log the prompt to the file
        log.info(f"USER_PROMPT: {query}")

        # Start processing the command
        processing_time_str = time.strftime("%H:%M:%S")
        print(Fore.CYAN + f"[{processing_time_str}] Processing command...")

        response = await self.get_response(query)
        self.chat_history.add_ai_message(response)

        responseMsg = String()
        responseMsg.data = response
        self.llm_response_pub.publish(responseMsg)

        processing_time_str = time.strftime("%H:%M:%S")
        print(Fore.CYAN + f"[{processing_time_str}] Response received...")


# ROS init and run
def main(args=None):
    rclpy.init(args=args)

    # Voice input/output node
    voice_io = VoiceInOut()
    # voice_io.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)

    # text input
    text_input_node = TextInput()
    text_thread = threading.Thread(target=text_input_node.get_query)
    text_thread.start()

    # Robot setting up
    spot = SpotController("spot")
    tello = TelloController("tello")

    agent = Agent(tello, tello.robot_name, voice_io)
    agent.add_robot(spot, spot.robot_name)

    #agent.set_current_robot(tello.robot_name)

    # Use executor in a separate thread
    executor = MultiThreadedExecutor()
    executor.add_node(agent)

    # Spin also the spot and tello controllers.
    executor.add_node(tello)
    executor.add_node(spot)

    # Text input
    executor.add_node(text_input_node)

    # Spin also the voice input/output node
    executor.add_node(voice_io)

    # Start the ROS spinning in a background thread
    spin_thread = threading.Thread(target=executor.spin)

    spin_thread.start()
    spin_thread.join()

    executor.shutdown()

    agent.destroy_node()
    # spot.destroy_node()
    text_input_node.destroy_node()
    tello.destroy_node()
    voice_io.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
