# camera_service.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class CameraRaw(Node):

    image_raw_topic = "/camera/image_raw"  # raw image frames from the drone's camera

    def __init__(self, name="camera_raw"):
        super().__init__(name)

        self.declare_parameter("image_raw_topic", self.image_raw_topic)

        self.image_raw_topic = (
            self.get_parameter("image_raw_topic").get_parameter_value().string_value
        )

        self.sub_raw = self.create_subscription(
            Image, self.image_raw_topic, self.image_callback, 5
        )

        self.image_raw = None

    def image_callback(self, msg):
        self.image_raw = msg

    def get_latest_image(self):
        if self.image_raw is None:
            self.get_logger().warn("No image received yet.")
            return None

        return self.image_raw
