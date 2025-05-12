import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

PKG_DIR = get_package_share_directory("robot_bt")


def create_bt_server_node(ld: LaunchDescription) -> None:
    params_file = LaunchConfiguration("params_file")

    argus_camera_node = Node(
        package="robot_bt",
        executable="bt_server",
        parameters=[params_file],
        output="screen",
    )

    ld.add_action(argus_camera_node)


def declare_arguments(ld: LaunchDescription) -> None:
    default_param_file = os.path.join(PKG_DIR, "config", "params.yaml")

    params_file_arg = DeclareLaunchArgument(
        "params_file",
        default_value=str(default_param_file),
        description="Parameters file to be used.",
    )

    ld.add_action(params_file_arg)


def generate_launch_description():
    ld = LaunchDescription()

    declare_arguments(ld)
    create_bt_server_node(ld)

    return ld
