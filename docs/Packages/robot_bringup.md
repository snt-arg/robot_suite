# Robot Bringup

---

When handling large projects in ROS2, launch files and configuration files are nice to have because they allow to easily run the system over different configurations. Launch files allow to run specific packages with different arguments. And these arguments can be defined in configuration files.

The `robot_bringup` package is designed to contain launch files for each robot platform. This provides a layer of abstraction, so that one doesn't have to manually execute each package, plugin of the `robot_suite` manually to interact with a robot. But with a bringup launch file, the user can just execute a signle launch file that will automatically start relevant drivers, packages and plugins for the robot platform.

---

## Launch files

Launch files allow to start different packages in a seamless way.

The `robot_bringup` package currently supports the following robot platforms :

1. Tello

```bash
ros2 launch robot_bringup tello_launch.py
```

2. Spot

```bash
ros2 launch robot_bringup spot_launch.py
```

In case you want to add a launch file for a new robot platform, please refer to [Add a robot](../Packages/add_a_robot.md).

!!! Tip

    Always make sure that your ROS2 workspace and environment are well sourced before executing a launch command.

---

## Configuration files

Configuration files allow to define values for the parameters of each node in our system. In launch files, it is possible to define which configuration file should be used for each node. This provides flexibility by allowing to execute the system with different configuration files depending of the use case.

To have a better understanding of the launch files and configuration files, let's explore a simple example.

---

## Simple example

!!! Example

    Consider an object detection system composed of :

    1. a driver (for image exchanges with a camera),
    1. a Graphical User Interface (GUI),
    1. an object detection plugin.

    Instead of manually starting each of the components above, it is possible to define a launch file that will automatically run the components, so that to launch the whole system, we only have to run the launch file.

    A simple use case would be topics names. Taking again the example of our simple object detection system. Let's say that the camera driver and the object detection plugin are two ROS2 nodes exchanging images captured by the camera over a ROS2 topic named '/images'. Then, instead of simply hardcoding the name of that topic in each node, it is better to provide the name of that topic via a configuration file, accessible to both nodes. In fact, the configuration file allow to dynamically change the name of that topic from execution to execution, without having to change the name of that topic in the code of each node.

    **Launch file**

    ```python
    from launch import LaunchDescription

    from launch_ros.actions import Node

    from launch.actions import DeclareLaunchArgument
    from launch.substitutions import LaunchConfiguration

    # Function to launch the driver, using our configuration file (param_file)
    def create_driver_launch(ld: LaunchDescription, param_file: LaunchConfiguration) -> None:
        ld.add_action(
            Node(
                package="driver",
                executable="camera_driver_node",
                parameters=[param_file],
            )
        )

    # Function to start the GUI for visualization
    def create_gui_launch(ld: LaunchDescription, param_file: LaunchConfiguration) -> None:
        ld.add_action(
            Node(
                package="gui",
                executable="gui_node",
                parameters=[param_file],
                output="screen",
            )
        )

    # Function to start the object detection plugin
    def create_object_detection_plugin_launch(ld: LaunchDescription, param_file: LaunchConfiguration) -> None:
        ld.add_action(
            Node(
            package="object_detection_plugin",
            executable="object_detection_node",
            parameters=[param_file],
        )
        )

    def generate_launch_description():
        ld = LaunchDescription()
        default_params_file = <path_to_configuration_file>
        parameters = DeclareLaunchArgument(
            "params_file", default_value=str(default_params_file)
        )
        param_file = LaunchConfiguration("params_file")

        # driver
        create_camera_driver_launch(ld, param_file)

        # GUI
        create_gui_launch(, param_file)

        # Plugin
        create_object_detection_plugin_launch(ld, param_file)

        return ld

    ```

    In the launch file, we start three nodes, the camera driver, the GUI and the object detection plugin. To each of these nodes, we provide the same configuration file, whose content could be as below:

    **Configuration file**

    ```yaml
    camera_driver_node:
        ros__parameters:
            image_topic: "/images"
            image_size: "640x480"

    gui_node:
        ros__parameters:
            image_topic: "/images"
            gui_theme: "dark"

    object_detection_node:
        ros__parameters:
            image_topic: "/images"
    ```

    In this configuration file, we defined the value of the `image_topic` as `"/images"` for all nodes. There are also node specific parameters such as `image_size`, that is defined only for the driver.

For more information, please refer to [ROS2 documention on launch files](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Launch-Main.html).
