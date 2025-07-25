# To handle ROS node
import rclpy
from rclpy.node import Node

# ROS image message
from sensor_msgs.msg import Image

# person tracked messages
from person_tracking_msgs.msg import Box

# To convert cv2 images to ROS Image messages
from cv_bridge import CvBridge

# To draw rectangles
import cv2


from person_tracking_helpers.helpers import calculate_midpoint_box


class DrawTarget(Node):

    # Topic names
    image_raw_topic = "/camera/image_raw"
    person_tracked_topic = "/person_tracked"
    image_annotated_hands_topic = "/hand/annotated/image"
    drawing_person_tracked_topic = "/camera/person_tracked"
    drawing_person_tracked_and_hands_topic = "/camera/hands/person_tracked"

    # subscribers
    sub_image_raw = None
    sub_person_tracked = None
    sub_annotated_hands = None

    # publishers
    publisher_drawing = None
    publisher_drawing_and_hands = None
    timer = None

    # publishing rate
    publishing_rate = 0.03  # 30 hertz

    def __init__(self, name):

        # Creating the Node
        super().__init__(name)

        # init topic names
        self._init_parameters()

        # init subscribers
        self._init_subscriptions()

        # init publishers
        self._init_publishers()

        # Used to convert cv2 frames into ROS Image messages and vice versa
        self.cv_bridge = CvBridge()

        # Variable to contain the coordinates of the person tracked (midpoint and coordinates of the bounding box)
        self.pilot_box = None

        # Variable to contain the image received from the drone
        self.image = None

        self.image_annotated_hands = None

        # Dimensions of the image
        self.image_height = None
        self.image_width = None

        self.update_time_raw = self.get_clock().now().nanoseconds

        self.update_time_hands_annotated = self.get_clock().now().nanoseconds

    def _init_parameters(self) -> None:
        """Method to initialize parameters such as ROS topics' names"""

        self.declare_parameter("image_raw_topic", self.image_raw_topic)
        self.declare_parameter("person_tracked_topic", self.person_tracked_topic)
        self.declare_parameter(
            "drawing_person_tracked_topic", self.drawing_person_tracked_topic
        )
        self.declare_parameter(
            "image_annotated_hands_topic", self.image_annotated_hands_topic
        )
        self.declare_parameter(
            "drawing_person_tracked_and_hands_topic",
            self.drawing_person_tracked_and_hands_topic,
        )
        self.declare_parameter("publishing_rate", self.publishing_rate)

        self.image_raw_topic = (
            self.get_parameter("image_raw_topic").get_parameter_value().string_value
        )

        self.person_tracked_topic = (
            self.get_parameter("person_tracked_topic")
            .get_parameter_value()
            .string_value
        )

        self.drawing_person_tracked_topic = (
            self.get_parameter("drawing_person_tracked_topic")
            .get_parameter_value()
            .string_value
        )
        self.image_annotated_hands_topic = (
            self.get_parameter("image_annotated_hands_topic")
            .get_parameter_value()
            .string_value
        )
        self.drawing_person_tracked_and_hands_topic = (
            self.get_parameter("drawing_person_tracked_and_hands_topic")
            .get_parameter_value()
            .string_value
        )

        self.publishing_rate = (
            self.get_parameter("publishing_rate").get_parameter_value().double_value
        )

    def _init_publishers(self) -> None:
        """Method to initialize publishers"""
        self.publisher_drawing = self.create_publisher(
            Image, self.drawing_person_tracked_topic, 10
        )
        self.publisher_drawing_and_hands = self.create_publisher(
            Image, self.drawing_person_tracked_and_hands_topic, 10
        )
        self.timer = self.create_timer(
            self.publishing_rate, self.drawing_person_tracked_callback
        )

    def _init_subscriptions(self) -> None:
        """Method to initialize subscriptions"""
        self.sub_image_raw = self.create_subscription(
            Image, self.image_raw_topic, self.image_raw_listener_callback, 5
        )
        self.sub_person_tracked = self.create_subscription(
            Box, self.person_tracked_topic, self.person_tracked_listener_callback, 5
        )
        self.sub_annotated_hands = self.create_subscription(
            Image,
            self.image_annotated_hands_topic,
            self.image_annotated_hands_callback,
            5,
        )

    ########################### First Subscriber ###########################################################################################
    #
    def image_raw_listener_callback(self, img_msg):
        """Callback function for the subscriber node (to topic /camera/image_raw).
        For each image frame, save it in a variable for processing"""
        self.get_logger().debug("Raw images received")
        self.image = self.cv_bridge.imgmsg_to_cv2(img_msg, "rgb8")

        self.update_time_raw = self.get_clock().now().nanoseconds

        # Dimensions of the image. Useful to denormalise bounding box coordinates
        if self.image_height is None or self.image_width is None:
            self.image_height, self.image_width, _ = self.image.shape

    def image_annotated_hands_callback(self, img_msg):
        """Callback function for the subscriber node (to topic "/hand/annotated/image").
        For each image frame, save it in a variable for processing"""

        self.get_logger().debug("Annotated hands images received")

        self.image_annotated_hands = self.cv_bridge.imgmsg_to_cv2(img_msg, "rgb8")
        self.update_time_hands_annotated = self.get_clock().now().nanoseconds

    def person_tracked_listener_callback(self, msg):
        """Callback function for the subscriber node (to topic /person_tracked).
        For each message received, save it in a variable for processing
        The messages contain the midpoint and coordinates of the bounding box around the target person
        midpoint : msg.midpoint
        coordinates : msg.top_left and msg.bottom_right"""
        self.get_logger().debug("Target person's position received")

        self.pilot_box = msg

    ######################### Publisher #####################################################################################################
    def drawing_person_tracked_callback(self):
        """This methods is the callback function for the publisher of images where
        ONLY the target person is highlighted."""

        if self.get_clock().now().nanoseconds - self.update_time_raw < 1e8:

            image_drawn = self.draw_rectangle(self.image)

            if image_drawn is not None:
                self.publisher_drawing.publish(
                    self.cv_bridge.cv2_to_imgmsg(image_drawn, "rgb8")
                )
                self.get_logger().debug("Publishing pilot person frameNones")

        else:
            self.get_logger().warning(
                "Haven't received raw frames since: "
                + str((self.get_clock().now().nanoseconds - self.update_time_raw) / 1e9)
                + " seconds",
            )

    def drawing_person_tracked_hands_callback(self):
        """This methods is the callback function for the publisher of images where
        ONLY the target person and HAND LANDMARKS are highlighted."""

        if (
            self.get_clock().now().nanoseconds - self.update_time_handsNone_annotated
            < 1e8
        ):
            image_drawn_and_hands = self.draw_rectangle(self.image_annotated_hands)

            if image_drawn_and_hands is not None:
                self.publisher_drawing_and_hands.publish(
                    self.cv_bridge.cv2_to_imgmsg(image_drawn_and_hands, "rgb8")
                )
                self.get_logger().debug("Publishing pilot person and hands frames")
        else:
            self.get_logger().warn(
                "Haven't received hand annotated frames since: ",
                str(
                    (
                        self.get_clock().now().nanoseconds
                        - self.update_time_hands_annotated
                    )
                )
                / 1e9,
                " seconds",
            )

    def draw_rectangle(self, image):
        if image is not None and self.pilot_box is not None:

            midpoint = calculate_midpoint_box(self.pilot_box)

            top_left_point_x = round(self.pilot_box.top_left.x * self.image_width)
            top_left_point_y = round(self.pilot_box.top_left.y * self.image_height)

            bottom_right_point_x = round(
                self.pilot_box.bottom_right.x * self.image_width
            )

            bottom_right_point_y = round(
                self.pilot_box.bottom_right.y * self.image_height
            )

            circle_center = (
                round(midpoint.x * self.image_width),
                round(midpoint.y * self.image_height),
            )

            # Drawing box
            cv2.rectangle(
                image,
                (top_left_point_x, top_left_point_y),
                (bottom_right_point_x, bottom_right_point_y),
                (86, 237, 81),
                1,
            )

            # Drawing midpoint circle
            cv2.circle(image, circle_center, 5, (86, 237, 81), -1)

            # drawing text annotation container
            cv2.rectangle(
                image,
                (top_left_point_x, top_left_point_y),
                (top_left_point_x + 3, top_left_point_y + 3)(86, 237, 81),
                -1,
            )

            # Box annotation
            cv2.putText(
                img=image,
                text="Target",
                org=(top_left_point_x + 1, top_left_point_y + 1),
                fontScale=1.0,
                color=(255, 255, 255),
                thickness=2,
            )

            return image

        return None


###################################################################################################################################


def main(args=None):
    # Initialization ROS communication
    rclpy.init(args=args)

    # Node instantiation
    draw_target = DrawTarget("pilot_person_drawer_llm_node")
    # draw_target.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)

    # Execute the callback function until the global executor is shutdown
    rclpy.spin(draw_target)

    # destroy the node. It is not mandatory, since the garbage collection can do it
    draw_target.destroy_node()

    rclpy.shutdown()
