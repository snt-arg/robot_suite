import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def create_object_detection_plugin_launch(
    ld: LaunchDescription, params_file: LaunchConfiguration
) -> None:

    object_detection_pck_dir = get_package_share_directory("object_detection_plugin")
    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    object_detection_pck_dir, "launch/object_detection_launch.py"
                )
            ),
            launch_arguments={
                "params_file": params_file,
            }.items(),
        )
    )


def create_object_following_plugin_launch(
    ld: LaunchDescription, params_file: LaunchConfiguration
) -> None:

    object_following_pck_dir = get_package_share_directory("object_following_plugin")
    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    object_following_pck_dir, "launch/object_following_launch.py"
                )
            ),
            launch_arguments={
                "params_file": params_file,
            }.items(),
        )
    )


def create_sign_filter_plugin_launch(
    ld: LaunchDescription, params_file: LaunchConfiguration
) -> None:

    sign_filter_pck_dir = get_package_share_directory("sign_filter_plugin")
    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(sign_filter_pck_dir, "launch/sign_filter_launch.py")
            ),
            launch_arguments={
                "params_file": params_file,
            }.items(),
        )
    )


def create_drawer_plugin_launch(
    ld: LaunchDescription, params_file: LaunchConfiguration
) -> None:

    drawer_pck_dir = get_package_share_directory("drawer_plugin")
    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(drawer_pck_dir, "launch/drawing_target_launch.py")
            ),
            launch_arguments={
                "params_file": params_file,
            }.items(),
        )
    )


def generate_launch_description():

    pkg_dir = get_package_share_directory("person_tracking_bringup")

    default_param_file = os.path.join(pkg_dir, "config", "params.yaml")

    parameters = DeclareLaunchArgument(
        "params_file", default_value=str(default_param_file)
    )
    params_file = LaunchConfiguration("params_file")

    ld = LaunchDescription()

    ld.add_action(parameters)
    create_object_detection_plugin_launch(ld, params_file)
    create_object_following_plugin_launch(ld, params_file)
    create_sign_filter_plugin_launch(ld, params_file)
    create_drawer_plugin_launch(ld, params_file)

    return ld
