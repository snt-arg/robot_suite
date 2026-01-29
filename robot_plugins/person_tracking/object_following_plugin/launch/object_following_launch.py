import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_dir = get_package_share_directory("object_following_plugin")

    default_params_file = os.path.join(pkg_dir, "config", "params.yaml")

    parameters = DeclareLaunchArgument(
        "params_file", default_value=str(default_params_file)
    )

    param_file = LaunchConfiguration("params_file")

    tracker_node = Node(
        package="object_following_plugin",
        executable="tracker_node",
        parameters=[param_file],
        output="log",
    )

    commands_node = Node(
        package="object_following_plugin",
        executable="following_commands_node",
        parameters=[param_file],
    )

    ld = LaunchDescription()
    ld.add_action(parameters)
    ld.add_action(tracker_node)
    ld.add_action(commands_node)

    return ld
