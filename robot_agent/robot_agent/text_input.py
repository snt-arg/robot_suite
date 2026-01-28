
from std_msgs.msg import String

from rclpy.node import Node

import time

import rclpy

import threading

import re



########################################## Voice Input Output Node ############################################################################
class TextInput(Node):
    """Simple node just to take input from the keyboard and send the user query. 
    That is to emulate the robot station behaviour while it is in development"""

    # Topic to publish the user's textual query
    user_query_topic = "/user_query"



    def __init__(self):
        super().__init__("TextInput_node")

        ##### PUBLISHERS AND SUBSCRIBERS
        self.user_query_pub = None

        ##### INITIALIZE PARAMETERS, PUBLISHERS, SUBSCRIPTIONS
        self._init_parameters()
        self._init_publishers()

    ########################################## Initialization Methods ############################################################################

    def _init_parameters(self) -> None:
        """Method to initialize parameters such as ROS topics' names"""
        self.declare_parameter("user_query_topic", self.user_query_topic)
        
        self.user_query_topic = (
            self.get_parameter("user_query_topic").get_parameter_value().string_value
        )


    def _init_publishers(self) -> None:
        """Method to initialize publishers"""
        self.user_query_pub = self.create_publisher(String, self.user_query_topic, 10)

   
    
    def get_query(self) -> None:
        """Method that waits for the user to enter something on the terminal and press enter to send the query"""
        
        while True:
            if rclpy.ok():
                query = input()
            
                query_msg = String()
                query_msg.data = query
                
                self.user_query_pub.publish(query_msg)
            else: 
                continue
    

