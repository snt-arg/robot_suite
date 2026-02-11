# How to add a robot?

At the moment, the `robot_suite` supports the following platforms:

- Tello
- Spot

However, it is possible to extend the `robot_suite` with new robots, so that it will be possible to execute the packages of the `robot_suite` on the new robot platform.  
Thus, to add a new platform, you can follow the steps below.

---

## Compatible driver

The first step is to make sure you have a compatible driver.

The plugins of the `robot_suite` rely on ROS2 topics and services to get status information from the robot, such as image frames, battery level and much more. As the functioning of these plugins depends on these information, it is crucial to have an ROS2 driver for the robot.

---

## Launch file

Launch file facilitate and automate the startup process of complex ROS2 systems. Since the `robot_suite` is composed of many , the launching procedure can easily become overwhelming, considering that robot requires specific a configuration of the packages. So we defined the `robot_bringup` package to launch robot specific packages automatically.  
In case you want to add a new robot, it will be easier to also sue a launch file to start the `robot_suite` for that specific robot.  
To define a launch file for a new robot, please refer to [ROS2 documentation](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Launch-Main.html).
You can also check our simple launch file example [here](../Packages/robot_bringup.md/#simple-example).

---

## Behaviour tree (Optional)

As explained in [Robot Behavior Tree](../Packages/robot_bt.md), behaviour trees allow to define various (contextual) behaviours for a robot. Hence, if you want to add a new robot to the `robot_suite` you can create a custom behaviour tree for that specific robot. The procedure to create a new behaviour tree is defined [here](../Packages/robot_bt.md/#creating-a-behavior-tree).

---

## Robot controller (Optional)

This is an optional step as it is required only if you want to use the `robot_agent` package.

The `robot_agent` package provides a natural language interface for interacting with an AI agent handling robots. The AI agent relies on a set of **tools** to manage robots, thus if a new robot is added, one has to provide the set of tools that the AI agent will use to manage that robot. This set of tool is what we call a **controller** for that robot.  
To add a new robot controller, please refer to [this section](../Packages/robot_agent.md/#adding-a-robot-controller).
