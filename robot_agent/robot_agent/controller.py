from rosa import RobotSystemPrompts
from langchain.agents import tool

from rclpy.node import Node

from abc import abstractmethod, ABC

from typing import List


class Controller(Node, ABC):

    @property
    @abstractmethod
    def robot_name(self) -> str:
        """Property giving the name of the robot. This allows to differentiate a robot from another, even if they are of the same type.
        For example, the name allows to differentiate a Tello drone from another Tello drone
        """
        raise NotImplementedError

    @abstractmethod
    def get_prompts(self) -> RobotSystemPrompts:
        """Method to return the contextual prompts for the agent. User RobotSystemPrompts to define the prompts"""
        raise NotImplementedError

    @abstractmethod
    def get_tools(self) -> List:
        """Method returning the set of tools for the robot. You can use langchain @tool flag to define each tool"""
        raise NotImplementedError
