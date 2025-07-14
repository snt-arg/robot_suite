import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_dir = get_package_share_directory("sign_filter_plugin")

    default_params_file = os.path.join(pkg_dir, "config", "params.yaml")

    parameters = DeclareLaunchArgument(
        "params_file", default_value=str(default_params_file)
    )

    params_file = LaunchConfiguration("params_file")

    sign_filter_node = Node(
        package="sign_filter_plugin",
        executable="sign_filter_node",
        parameters=[params_file],
    )

    ld = LaunchDescription()
    ld.add_action(parameters)
    ld.add_action(sign_filter_node)

    return ld
