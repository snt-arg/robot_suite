from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python import get_package_share_directory
from launch.conditions import IfCondition


def republish_compressed_image(
    in_topic: str, out_topic: str, compression_flag_name: str = "use_compression"
):

    compressed_image_node = Node(
        package="image_transport",
        executable="republish",
        arguments=["raw", "compressed"],
        remappings=[
            ("in", in_topic),
            ("out/compressed", out_topic),
        ],
        condition=IfCondition(LaunchConfiguration(compression_flag_name)),
    )

    return compressed_image_node


def generate_compression_flag(compression_flag_name: str = "use_compression"):
    compression_flag = DeclareLaunchArgument(
        compression_flag_name,
        default_value="true",
        description="If true, the images will be republished as compressed images on a separate topic",
    )

    return compression_flag
