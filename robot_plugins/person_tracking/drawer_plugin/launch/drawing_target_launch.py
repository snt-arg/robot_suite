import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition


def generate_launch_description():
    pkg_dir = get_package_share_directory("drawer_plugin")

    default_param_file = os.path.join(pkg_dir, "config", "params.yaml")

    parameters = DeclareLaunchArgument(
        "params_file", default_value=str(default_param_file)
    )

    param_file = LaunchConfiguration("params_file")

    drawer_node = Node(
        package="drawer_plugin",
        executable="drawer_node",
        parameters=[param_file],
    )

    compression_flag = DeclareLaunchArgument(
        "use_compression",
        default_value="true",
        description="If true, the images will be republished as compressed images on a separate topic",
    )

    compressed_image_node_target = Node(
        package="image_transport",
        executable="republish",
        arguments=["raw", "compressed"],
        remappings=[
            ("in", "/camera/person_tracked"),
            ("out/compressed", "/camera/person_tracked/compressed"),
        ],
        condition=IfCondition(LaunchConfiguration("use_compression")),
    )

    compressed_image_node_target_hands = Node(
        package="image_transport",
        executable="republish",
        arguments=["raw", "compressed"],
        remappings=[
            ("in", "/camera/hands/person_tracked"),
            ("out/compressed", "/camera/hands/person_tracked/compressed"),
        ],
        condition=IfCondition(LaunchConfiguration("use_compression")),
    )

    ld = LaunchDescription()
    ld.add_action(parameters)
    ld.add_action(drawer_node)
    ld.add_action(compression_flag)
    ld.add_action(compressed_image_node_target)
    ld.add_action(compressed_image_node_target_hands)

    return ld
