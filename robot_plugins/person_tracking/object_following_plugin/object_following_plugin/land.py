# for handling ROS node
import rclpy

from rclpy.node import Node


# ROS Twist message import. This message type is used to send commands to the drone.
from std_msgs.msg import String, Empty


class LandTello(Node):

    # publishers
    publisher_commands = None
    key_pressed_topic = "/key_pressed"
    land_topic = "/land"

    def __init__(self, name):
        # Creating the Node
        super().__init__(name)

        # init topic names
        self._init_parameters()

        # init subscribers
        self._init_subscribers()

        # init publishers
        self._init_publishers()

        self.sub_key_pressed = None

    def _init_parameters(self) -> None:
        """Method to initialize parameters such as ROS topics' names"""

        # Topic names
        self.declare_parameter("key_pressed_topic", self.key_pressed_topic)
        self.declare_parameter("land_topic", self.land_topic)

        self.key_pressed_topic = (
            self.get_parameter("key_pressed_topic").get_parameter_value().string_value
        )

        self.land_topic = (
            self.get_parameter("land_topic").get_parameter_value().string_value
        )

    def _init_subscribers(self) -> None:
        """Method to initialize publishers"""

        # publishers
        self.sub_key_pressed = self.create_subscription(
            String, self.key_pressed_topic, self.key_pressed_callback, 5
        )

    def _init_publishers(self) -> None:
        """Method to initialize publishers"""

        # publishers
        self.publisher_commands = self.create_publisher(Empty, self.land_topic, 10)

    ######################### Publisher #####################################################################################################
    def key_pressed_callback(self, msg: String) -> None:
        """Callback function to handle the key pressed event."""
        if msg.data == "l":
            # Publish the message to the takeoff topic
            self.publisher_commands.publish(Empty())
            self.get_logger().info("Land command sent")


###################################################################################################################################


def main(args=None):
    # Intialization ROS communication
    rclpy.init(args=args)
    land_tello = LandTello("Land_Tello_node")

    # execute the callback function until the global executor is shutdown
    rclpy.spin(land_tello)

    # destroy the node. It is not mandatory, since the garbage collection can do it
    land_tello.destroy_node()

    rclpy.shutdown()
