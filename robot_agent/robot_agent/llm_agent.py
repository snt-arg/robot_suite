import pkgutil, inspect
import importlib
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

from robot_agent.controller import Controller
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

    def __init__(self, voice_node: Node = None):
        super().__init__("RoboticAgent")

        self.agent_tools = self._get_agent_tools()

        self.llm_model = None
        self._init_model()

        self.llm_response_pub = None
        self.user_query_sub = None
        self.change_robot_sub = None

        self.robots = dict()

        self.rosa = ROSA(
            ros_version=2,
            llm=self.llm_model,
            streaming=True,
            tools=self.agent_tools,
        )

        self.chat_history = ChatMessageHistory(messages=[])

        self.current_robot_name = None

        self.event_loop = asyncio.new_event_loop()

        self.event_loop_thread = threading.Thread(
            target=self.event_loop.run_forever, daemon=True
        )
        self.event_loop_thread.start()

        # self.add_robot(robot_node, robot_name)
        # to set the current robot, make sure that the llm model was already initialized
        # self.set_current_robot(robot_name)

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

    def add_robot(self, robot_controller: Controller, robot_name: str):

        if robot_name not in self.robots:
            robot_dict = dict()
            robot_dict["robot_tools"] = robot_controller.get_tools()
            robot_dict["robot_prompts"] = robot_controller.get_prompts()
            robot_dict["robot_controller_node"] = robot_controller
            self.robots[robot_name] = robot_dict
        else:

            self.get_logger().warn(
                f"Robot already exists in our list of known robots: {list(self.robots)}"
            )

    def remove_robot(self, robot_name):
        if robot_name in self.robots:
            self.robots.pop(robot_name)

            if self.current_robot_name == robot_name:
                self.current_robot_name = None
                self.rosa = ROSA(
                    ros_version=2,
                    llm=self.llm_model,
                    streaming=True,
                    tools=self.agent_tools,
                )

                return "Done! The robot removed was the current robot. So the user should set the current robot to another robot."
            return "Done, the robot was removed from known robots."

        else:
            self.get_logger().warn(
                f"Robot doesn't exist in our list of known robots: {list(self.robots.keys())}"
            )
            return f"Robot doesn't exist in our list of known robots: {list(self.robots.keys())}"

    def set_current_robot(self, robot_name):
        if robot_name in self.robots:
            self.current_robot_name = robot_name
            self.rosa = ROSA(
                ros_version=2,
                llm=self.llm_model,
                streaming=True,
                tools=self.robots[robot_name]["robot_tools"] + self.agent_tools,
                prompts=self.robots[robot_name]["robot_prompts"],
            )

            return f"The current robot is now {self.current_robot_name}"

        else:
            self.get_logger().error(
                f"Robot {robot_name} doesn't exist. Make sure to add {robot_name} first."
            )
            return f"Robot {robot_name} doesn't exist. Make sure to add {robot_name} first."

    ########################################## Subscriber callback ############################################################################
    def user_query_callback(self, msg) -> None:
        """Callback for the subscriber node (to topic self.user_query_topic).
        Receives user query messages."""
        self.user_query = msg.data
        self.chat_history.add_user_message(self.user_query)

        if self.rosa is not None:
            asyncio.run_coroutine_threadsafe(self.send_query(msg.data), self.event_loop)

        if self.current_robot_name is None:
            self.get_logger().warn(
                f'\033[33m Received this user query : "\033[94m \033[1m {self.user_query} \033[22m \033[33m", \n but the current robot is not yet initialized'
                f"\nThe list of available robots is {list(self.robots)}."
                f"\nYou can set the current robot to one of these to proceed.\n"
            )

    def change_current_robot(self, new_robot_name) -> None:
        """Method to change the current robot to another robot (new_robot_name).
        If the current robot is not defined, it simply sets the current robot to the new robot.
        """
        if new_robot_name in self.robots:
            if (
                self.current_robot_name is None
                or new_robot_name != self.current_robot_name
            ):
                self.set_current_robot(new_robot_name)
                self.get_logger().debug(f"Switched to robot: {new_robot_name}")

                return f"Switched to robot: {new_robot_name}"
            else:
                self.get_logger().info(f"Already using robot: {new_robot_name}")

                return f"The current robot was already: {new_robot_name}"

        else:
            self.get_logger().warn(
                f"Robot '{new_robot_name}' not found. Available robots: {list(self.robots.keys())}"
            )

            return f"Robot '{new_robot_name}' not found. Known robots are: {list(self.robots.keys())}. the user should choose from that list."

    def change_robot_callback(self, msg) -> None:
        """Callback for the subscriber node (to topic self.change_robot_topic).
        Receives the name of the robot to switch to.
        """
        new_robot_name = msg.data.strip()

        self.change_current_robot(new_robot_name)

    def load_robots(self):
        """Method to load all available robot controllers and pass them to our agent"""
        robots_loaded = []
        robot_files_not_loaded = []

        controllers_module = importlib.import_module(".controllers", __package__)
        for p in pkgutil.iter_modules(controllers_module.__path__):
            robot_controller_file_name = p[1]
            try:
                robot_controller_file = importlib.import_module(
                    ".controllers." + robot_controller_file_name, __package__
                )
                for _, robot_controller_cls in inspect.getmembers(
                    robot_controller_file, inspect.isclass
                ):
                    if (
                        robot_controller_cls.__module__
                        == robot_controller_file.__name__
                        and issubclass(robot_controller_cls, Controller)
                    ):
                        robot_controller_node = robot_controller_cls()
                        self.add_robot(
                            robot_controller_node, robot_controller_node.robot_name
                        )
                        robots_loaded.append(robot_controller_node.robot_name)

            except Exception as e:
                self.get_logger().warn(
                    f"An error occured while trying to load {robot_controller_file_name}: {e}"
                )
            robot_files_not_loaded.append(robot_controller_file_name)

        return f"Robots loaded: {robots_loaded}, files that couldn't be loaded: {robot_files_not_loaded}"

    def stop_tts_callback(self, request, response):
        """Callback method to stop Piper TTS when requested via service"""
        # Set the flag to False to stop Piper TTS
        try:
            self.try_stop_tts()
            response.success = True
            return response
        except Exception as e:
            self.get_logger().error(f"An error occurred while trying to stop TTS: {e}")
            response.success = False
            return response

    def try_stop_tts(self):
        self.voice_node.stop_tts = True
        self.get_logger().debug("stop_tts set to True")

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

        try:
            if self.rosa is not None:
                response = await self.get_response(query)
                self.chat_history.add_ai_message(response)

                responseMsg = String()
                responseMsg.data = response
                self.llm_response_pub.publish(responseMsg)

                processing_time_str = time.strftime("%H:%M:%S")
                print(Fore.CYAN + f"[{processing_time_str}] Response received...")
            else:
                raise Exception(
                    "ROSA is None. Make sure that the current robot is defined."
                )
        except Exception as e:
            self.get_logger().error(
                f"An exception occured when sending the user's query to the ROSA : {e}"
            )

    ##################################### LLM Agent tools ########################################################################
    # These are tools for handling which robot the agent is impersonating
    def _get_agent_tools(self):

        @tool
        def get_current_robot():
            """Tool to get the name of the current robot that the agent is impersonating."""
            if self.current_robot_name is not None:
                return self.current_robot_name
            else:
                return "The current robot is not yet defined"

        @tool
        def get_available_robots():
            """Tool to get the list of available/known robots that the agent can impersonate.
            This returns the list of robots names. Use it only when you need to know the list of available robot names.
            """
            return "The known robots are: " + str(list(self.robots.keys()))

        @tool
        def change_current_robot(new_robot_name):
            """Tool to change the current robot that the agent is impersonating to another robot from the list of available robots.
            Based on the robot provided as input, you should pass the correct robot name to this tool to change the current robot to that robot.
            The list of available robots can be retrieved using the tool `get_available_robots()`.

            :param new_robot_name: the name of the robot to change to. It is a Python string.
            """
            return self.set_current_robot(new_robot_name)

        @tool
        def load_robot_controllers():
            """
            This tool loads all the available robot controllers and adds them to the agent's list of known robots.
            This will load the robots even if they were already loaded before.
            This tool is not working properly yet. Use with caution!
            """
            ## This tool is not working properly yet. Use with caution!
            return self.load_robots()

        @tool
        def remove_robot_controller(robot_name):
            """
            Tool to remove a robot controller from the agent's list of known robots.
            If the removed robot was the current robot, the current robot will be set to None and the user should be asked to set the current robot to another robot from the list of known robots.
            Based on the robot provided as input, you should pass the correct robot name to this tool to remove that robot from the list of known robots.
            The list of known robots can be retrieved using the tool `get_available_robots()`.

            :param robot_name: the name of the robot to remove from the list of known robots. It is a Python string.
            """
            return self.remove_robot(robot_name)

        @tool
        def stop_tts():
            """Tool to stop audio reading of your response.
            This is useful in case the user wants to interrupt TTS.
            When using this tool, make sure to return an empty response to the user, that is, always answer with an empty string.
            """
            try:
                self.try_stop_tts()
                return "The TTS should stop soon. But don't tell the user. Answer with an empty string."
            except Exception as e:
                return f"We couldn't stop TTS because an error occured: {e}"

        return [
            get_current_robot,
            get_available_robots,
            change_current_robot,
            load_robot_controllers,
            remove_robot_controller,
            stop_tts,
        ]


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

    agent = Agent(voice_io)
    # Use executor in a separate thread
    executor = MultiThreadedExecutor()
    agent.load_robots()

    executor.add_node(agent)
    for robot_name in agent.robots:
        executor.add_node(agent.robots[robot_name]["robot_controller_node"])

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
    text_input_node.destroy_node()
    voice_io.destroy_node()
    for robot_name in agent.robots:
        agent.robots[robot_name]["robot_controller_node"].destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
