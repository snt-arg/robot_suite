################################### Imports #######################################

#for handling ROS node
import rclpy

#----- ROS image messages : 

    # for tracking info
from std_msgs.msg import String 

    # custom message to send bounding boxes
from person_tracking_msgs.msg import AllBoundingBoxes


#----- Utilities 

    # for converting tracking info in JSON format
import json

    # node base for behaviour tree
from plugin_base.plugin_base import PluginNode, NodeState

    # custom helper functions
from person_tracking_helpers.helpers import assign_objects_to_persons, construct_JSON_string

from typing import Optional, Any


class PersonObjectAssociation(PluginNode):
    person_classes = ["person"] # person class names
    objects = ["cell phone"] # list of objects 

    # overlapping method
    overlapping_method = "intersection"

    # topic names
    bounding_boxes_topic = "/all_bounding_boxes" # list of person bounding boxes
    tracking_info_topic = "/tracking_info" # topic to publish the information on persons and objects for llm-base commands package

    #ROS Subscriptions
    sub_boxes = None
    
    #ROS Publishers
    publisher_tracking_info = None

    def __init__(self,name):

        #Creating the Node
        super().__init__(name)

        #init topic names
        self._init_parameters()

        #init subscribers
        self._init_subscriptions()
        
        #init publishers
        self._init_publishers()


        #Variable containing all bounding boxes' coordinates for a single frame
        self.boxes = None

        # Variable to contain the tracking info in JSON format
        self.json_string_msg = None

        self.counter = 0

        
################################ Init functions ##################################################################################
    def _init_parameters(self)->None:
        """Method to initialize parameters such as ROS topics' names """

        #Topic names
        self.declare_parameter("bounding_boxes_topic", self.bounding_boxes_topic )
        self.declare_parameter("tracking_info_topic",self.tracking_info_topic)

        # others 
        self.declare_parameter("overlapping_method",self.overlapping_method)


        self.bounding_boxes_topic = (
        self.get_parameter("bounding_boxes_topic").get_parameter_value().string_value
        )
        self.tracking_info_topic = (
        self.get_parameter("tracking_info_topic").get_parameter_value().string_value
        ) 

        self.overlapping_method = (
        self.get_parameter("overlapping_method").get_parameter_value().string_value
        ) 

           
    def _init_publishers(self)->None:
        """Method to initialize publishers"""
        self.publisher_tracking_info = self.create_publisher(String,self.tracking_info_topic,5)
        

    def _init_subscriptions(self)->None:
        """Method to initialize subscriptions"""
        self.sub_boxes = self.create_subscription(AllBoundingBoxes,self.bounding_boxes_topic, self.listener_callback,5)



########################### Callback functions ###########################################################################################   
    def listener_callback(self, boxes_msg)->None:
        """Callback function for the subscriber node (to topic all_bounding_boxes).
        The received boxes are saved for further processing.
        """

        self.boxes = boxes_msg

        # Logs
        self.get_logger().info(f"Bounding boxes received N°{self.counter} received.")
        self.counter += 1
        
      
        
    def map_person_to_objects(self)->None:
        """Function to perform person object detection on a single frame.
        It saves the coordinates of all bounding boxes of persons detected on the frame in a variable named self.boxes"""
        
        # Initializing tracking info message
        self.json_string_msg = String()

        # temporary variable to contain the list of all objects detected
        tmp_list_object = []

        #temporary variable to contain the list of all person detected
        tmp_list_person = []

        # dictionnary to map each object to its possessor (the person whose bounding box shares the biggest area with the object's bounding box)
        possessor_to_objects_dict = dict()

        if self.boxes is not None:
            # For loop to get all go through all detections (persons and objects)
            for box in self.boxes.bounding_boxes:  
            
                # If the detection is a person
                if box.box_class in self.person_classes:

                    # Adding the person to the temporary list of all persons
                    tmp_list_person.append(box)

                # if the detection is an object 
                else:
                    #Adding the object to the temporary list of objects
                    tmp_list_object.append(box) 

            possessor_to_objects_dict = assign_objects_to_persons(tmp_list_person, tmp_list_object, self.overlapping_method)
            
            #print(f"\n## Possessors : {possessor_to_objects_dict}\n") #<--- to debug
            
            # JSON string message to send to LLM command interpreter
            self.json_string_msg.data = construct_JSON_string(tmp_list_person,possessor_to_objects_dict)

            self.get_logger().info(str(self.json_string_msg.data))

        else:
            self.get_logger().info(f"*** Didn't receive boxes to produce the mapping of person to objects ***\n")



######################## Publisher #####################################################################################  
    def publish_person_objects(self)->None:
        """Callback function for the publisher to the /tracking_info topic.
        A list of the coordinates of the bounding boxes around persons, persons ID and the objects they have on them"""
        if self.json_string_msg is not None:
            self.publisher_tracking_info.publish(self.json_string_msg)
            self.get_logger().info(f"\n\nJSON string sent to the LLM command interpreter : {self.json_string_msg.data}\n")



    def tick(self,blackboard: Optional[dict["str", Any]] = None) -> NodeState:
        """This method is a mandatory for PluginBase node. It defines what we want our node to do.
        It gets called 20 times a second if state=RUNNING
        Here we call callback functions to publish a detection frame and the list of bounding boxes.
        """
        self.map_person_to_objects()
        self.publish_person_objects()
        
        return NodeState.SUCCESS


def main(args=None):
    #Initialization of ROS communication  
    rclpy.init(args=args)

    #Node instantiation
    associator = PersonObjectAssociation('person_object_association_node')

    #execute the callback function until the global executor is shutdown
    rclpy.spin(associator)

    #destroy the node. It is not mandatory, since the garbage collection can do it
    associator.destroy_node()
    
    rclpy.shutdown()        
