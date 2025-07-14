import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition


def generate_launch_description():
    pkg_dir = get_package_share_directory("object_detection_plugin")

    default_params_file = os.path.join(pkg_dir, "config", "params.yaml")

    parameters = DeclareLaunchArgument(
        "params_file", default_value=str(default_params_file)
    )

    params_file = LaunchConfiguration("params_file")

    object_detection_node = Node(
        package="object_detection_plugin",
        executable="object_detection_node",
        parameters=[params_file],
    )

    run_associator_flag = DeclareLaunchArgument(
        "run_associator",
        default_value="false",
        description="If true, the associator node will run, publishing the list of detected persons and their objects",
    )

    person_association_node = Node(
        package="object_detection_plugin",
        executable="associator_node",
        parameters=[params_file],
        condition=IfCondition(LaunchConfiguration("run_associator")),
    )

    compression_flag = DeclareLaunchArgument(
        "use_compression",
        default_value="true",
        description="If true, the images will be republished as compressed images on a separate topic",
    )

    compressed_image_node = Node(
        package="image_transport",
        executable="republish",
        arguments=["raw", "compressed"],
        remappings=[
            ("in", "/camera/all_detected"),
            ("out/compressed", "/camera/all_detected/compressed"),
        ],
        condition=IfCondition(LaunchConfiguration("use_compression")),
    )

    ld = LaunchDescription()
    ld.add_action(parameters)
    ld.add_action(object_detection_node)
    ld.add_action(run_associator_flag)
    ld.add_action(person_association_node)
    ld.add_action(compression_flag)
    ld.add_action(compressed_image_node)

    return ld
