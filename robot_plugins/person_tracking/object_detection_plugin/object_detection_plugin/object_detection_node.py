################################### Imports #######################################

# for handling ROS node
import rclpy

# ----- ROS image messages :

# for camera frames
from sensor_msgs.msg import Image

# custom message to send bounding boxes
from person_tracking_msgs.msg import AllBoundingBoxes, Box


# ----- Utilities

# for converting cv2 images to ROS Image messages and vice versa
from cv_bridge import CvBridge


# node base for behaviour tree
from plugin_base.plugin_base import PluginNode, NodeState
from typing import Optional, Any


# YOLOv8 object detection framework
from ultralytics import YOLO


# for sending model to gpu if available
import torch


class ObjectDetector(PluginNode):

    # object detection model // Example topic for annotated hands
    model_type = "yolo"
    model_name = "yolo11n.pt"  #'v5lite-c.pt'
    model = None
    device = None

    # classes of interest (for detection)
    person_classes = ["person"]  # person class names
    objects = [
        "cell phone",
        "backpack",
        "book",
        "laptop",
        "handbag",
        "bottle",
        "umbrella",
        "banana",
        "apple",
    ]  # list of objects
    classes = None

    # minimum confidence probability for a detection to be accepted
    minimum_prob = 0.4

    # Variable to perform object detection on only some frames
    process_interval = 1e5

    # topic names
    image_raw_topic = "/camera/image_raw"  # raw image frames from the drone's camera
    all_detected_topic = "/camera/all_detected"  # image frames in which all persons (and specified objects) are detected
    bounding_boxes_topic = "/all_bounding_boxes"  # list of person bounding boxes

    # ROS Subscriptions
    sub_raw = None

    # ROS Publishers
    publisher_all_detected = None
    publisher_bounding_boxes = None

    def __init__(self, name):

        # Creating the Node
        super().__init__(name)

        # init model
        self._init_model()

        # init topic names
        self._init_parameters()

        # init subscribers
        self._init_subscriptions()

        # init publishers
        self._init_publishers()

        # ids of our classes of interest
        self.classes_needed = self.person_classes + self.objects

        self.classes_ID = [
            k for k, v in self.classes.items() if v.lower() in self.classes_needed
        ]

        # to convert cv2 images to Ros Image messages and vice versa
        self.cv_bridge = CvBridge()

        # Variable to contain the frame coming directly from the drone
        self.image_raw = None

        # Variable containing the time most recent time in nanoseconds when we received a raw image
        self.last_received_time = None

        # Variable to hold each frame after object detection. It contains all persons detected
        self.image_all_detected = None

        # Variable containing all bounding boxes' coordinates for a single frame
        self.boxes = None

    ################################ Init functions ##################################################################################
    def _init_model(self) -> None:
        """Method to initialize the object detection model based on its type and name.
        Right now, one single type is supported : 'yolo'"""
        match self.model_type.lower():

            case "yolo":
                self.model = YOLO(self.model_name)
                # using gpu is available
                self.device = torch.device(
                    "cuda" if torch.cuda.is_available() else "cpu"
                )
                self.model.to(self.device)
                self.classes = self.model.names

            case _:
                raise Exception("Unknown model type !")

    def _init_parameters(self) -> None:
        """Method to initialize parameters such as ROS topics' names"""

        # Topic names
        self.declare_parameter("image_raw_topic", self.image_raw_topic)
        self.declare_parameter("all_detected_topic", self.all_detected_topic)
        self.declare_parameter("bounding_boxes_topic", self.bounding_boxes_topic)

        # model
        self.declare_parameter("model_type", self.model_type)
        self.declare_parameter("model_name", self.model_name)

        # classes
        self.declare_parameter("person_classes", self.person_classes)
        self.declare_parameter("objects", self.objects)

        # other
        self.declare_parameter("minimum_prob", self.minimum_prob)
        self.declare_parameter("process_interval", self.process_interval)

        self.image_raw_topic = (
            self.get_parameter("image_raw_topic").get_parameter_value().string_value
        )

        self.all_detected_topic = (
            self.get_parameter("all_detected_topic").get_parameter_value().string_value
        )

        self.bounding_boxes_topic = (
            self.get_parameter("bounding_boxes_topic")
            .get_parameter_value()
            .string_value
        )

        self.model_type = (
            self.get_parameter("model_type").get_parameter_value().string_value
        )

        self.model_name = (
            self.get_parameter("model_name").get_parameter_value().string_value
        )

        self.person_classes = (
            self.get_parameter("person_classes")
            .get_parameter_value()
            .string_array_value
        )

        self.objects = (
            self.get_parameter("objects").get_parameter_value().string_array_value
        )

        self.minimum_prob = (
            self.get_parameter("minimum_prob").get_parameter_value().double_value
        )

        self.process_interval = (
            self.get_parameter("process_interval").get_parameter_value().double_value
        )

    def _init_publishers(self) -> None:
        """Method to initialize publishers"""
        self.publisher_all_detected = self.create_publisher(
            Image, self.all_detected_topic, 5
        )
        self.publisher_bounding_boxes = self.create_publisher(
            AllBoundingBoxes, self.bounding_boxes_topic, 5
        )

    def _init_subscriptions(self) -> None:
        """Method to initialize subscriptions"""
        self.sub_raw = self.create_subscription(
            Image, self.image_raw_topic, self.listener_callback, 5
        )

    ########################### Callback functions ###########################################################################################

    def listener_callback(self, img) -> None:
        """Callback function for the subscriber node (to topic /camera/image_raw).
        For each image processed, it saves in the log that an image has been processed.
        Then converts that image into cv2 format before performing object detection on that image and saving
        the result in self.image_all_detected"""

        self.last_received_time = self.get_clock().now().nanoseconds

        # converting ROS Image message to cv2 image
        self.image_raw = self.cv_bridge.imgmsg_to_cv2(img, "rgb8")

    def detection(self, frame) -> None:
        """Function to perform person object detection on a single frame.
        It saves the coordinates of all bounding boxes of persons detected on the frame in a variable named self.boxes
        """

        # detection of persons & objects in the frame. Only detections with a certain confidence level (minimum_prob) are  considered.
        results = self.model.track(
            frame, persist=True, classes=self.classes_ID, conf=self.minimum_prob
        )

        # Initializing all bounding boxes messages
        self.boxes = AllBoundingBoxes()

        # For loop to get all go through all detections (persons and objects)
        for yolo_box in results[0].boxes:

            # class of the detection (person, cell phone, ...)
            box_class = self.classes[yolo_box.cls.item()].lower()

            # if there is an id assigned by the YOLO model, we save it
            box_id = None
            if yolo_box.id is not None:
                box_id = int(yolo_box.id.item())

            else:
                box_id = -1

            # coordinates of the bounding box (top left and bottom right)
            ros_box = self.yolo_box_to_Box_msg(
                yolo_box.xyxyn[0].tolist(), box_class, box_id
            )  # normalized coordinates (within 0 and 1)

            self.boxes.bounding_boxes.append(ros_box)

        # returning the image where bounding boxes are displayed
        self.image_all_detected = results[0].plot()

    ######################## Publisher #####################################################################################
    def all_detected_callback(self) -> None:
        """
        callback funtion for the publisher node (to topic /camera/image_detected).
        The image on which object detection has been performed (self.image_all_detected) is published on the topic '/all_detected'
        """

        # processing only a some frames to reduce computing power consumption
        if self.last_received_time is not None and (
            (self.get_clock().now().nanoseconds - self.last_received_time)
            > self.process_interval
        ):

            self.detection(self.image_raw)  # performing detection on the cv2 image

            try:
                self.publisher_all_detected.publish(
                    self.cv_bridge.cv2_to_imgmsg(self.image_all_detected, "rgb8")
                )
                self.get_logger().debug("Publishing a frame on all detected topic")
            except Exception as e:
                self.get_logger().error("An error occured, ", e)
        else:
            self.get_logger().debug(
                "No raw images received yet. Cannot perform object detection"
            )

    def bounding_boxes_callback(self) -> None:
        """
        callback funtion for the publisher node (to topic /all_bounding_boxes).
        A list of the coordinates of bounding boxes around persons detected on the frame is published.
        """
        if self.boxes is None:
            self.get_logger().debug(
                "Can't publish bounding boxes. No information received yet"
            )
        else:
            self.publisher_bounding_boxes.publish(self.boxes)
            self.get_logger().debug(
                "\n##############################################\nPublishing a bounding boxes list\n\n"
            )

    def yolo_box_to_Box_msg(self, yolo_box, yolo_class, yolo_id):
        """Function to convert a yolo box (in list format) to a Box message"""
        box_msg = Box()

        box_msg.top_left.x = yolo_box[0]
        box_msg.top_left.y = yolo_box[1]
        box_msg.bottom_right.x = yolo_box[2]
        box_msg.bottom_right.y = yolo_box[3]

        box_msg.box_class = yolo_class
        box_msg.box_id = yolo_id

        return box_msg

    def tick(self, blackboard: Optional[dict["str", Any]] = None) -> NodeState:
        """This method is a mandatory for PluginBase node. It defines what we want our node to do.
        It gets called 20 times a second if state=RUNNING
        Here we call callback functions to publish a detection frame and the list of bounding boxes.
        """

        self.all_detected_callback()
        self.bounding_boxes_callback()

        return NodeState.SUCCESS


def main(args=None):
    # Initialization of ROS communication
    rclpy.init(args=args)

    # Node instantiation
    detector = ObjectDetector("object_detection_node")

    # execute the callback function until the global executor is shutdown
    rclpy.spin(detector)

    # destroy the node. It is not mandatory, since the garbage collection can do it
    detector.destroy_node()

    rclpy.shutdown()
