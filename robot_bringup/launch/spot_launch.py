import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import (
    PythonLaunchDescriptionSource,
    AnyLaunchDescriptionSource,
)
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def create_spot_driver_launch(ld: LaunchDescription, pkg_dir: str) -> None:
    spot_driver_pkg_dir = get_package_share_directory("spot_driver")

    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(spot_driver_pkg_dir, "launch/spot_driver.launch.py")
            ),
            launch_arguments={
                "config_file": os.path.join(pkg_dir, "config/spot_driver_params.yaml")
            }.items(),
        )
    )


def create_robot_bt_launch(ld: LaunchDescription) -> None:
    robot_bt_pkg_dir = get_package_share_directory("robot_bt")
    pkg_dir = get_package_share_directory("robot_bringup")
    params_file = os.path.join(pkg_dir, "config", "spot_params.yaml")

    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(robot_bt_pkg_dir, "launch/robot_bt_launch.py")
            ),
            launch_arguments={
                "params_file": params_file,
            }.items(),
        )
    )


def create_hand_tracker_plugin_launch(ld: LaunchDescription) -> None:
    pkg_dir = get_package_share_directory("robot_bringup")
    params_file = os.path.join(pkg_dir, "config", "spot_params.yaml")
    hand_tracker_pck_dir = get_package_share_directory("hand_gestures")
    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(hand_tracker_pck_dir, "launch/hand_gestures_launch.py")
            ),
            launch_arguments={
                "params_file": params_file,
                "run_annotator": "true",
                "use_compression": "true",
            }.items(),
        )
    )


def create_person_tracking_plugin_launch(ld: LaunchDescription) -> None:
    pkg_dir = get_package_share_directory("robot_bringup")
    params_file = os.path.join(pkg_dir, "config", "spot_params.yaml")
    person_tracking_pck_dir = get_package_share_directory("person_tracking_bringup")
    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    person_tracking_pck_dir, "launch/person_tracking_launch.py"
                )
            ),
            launch_arguments={
                "params_file": params_file,
                "run_associator": "true",
                "use_compression": "true",
            }.items(),
        )
    )


def create_robot_agent_plugin_launch(ld: LaunchDescription) -> None:
    pkg_dir = get_package_share_directory("robot_bringup")
    default_params_file = os.path.join(pkg_dir, "config", "spot_params.yaml")

    parameters = DeclareLaunchArgument(
        "params_file", default_value=str(default_params_file)
    )

    params_file = LaunchConfiguration("params_file")
    ld.add_action(parameters)

    ld.add_action(
        Node(
            package="robot_agent",
            executable="spot_controller_node",
            parameters=[params_file],
            prefix="gnome-terminal --",
        )
    )


def create_video_interface_launch(ld: LaunchDescription) -> None:
    ld.add_action(
        ExecuteProcess(
            cmd=["npm", "run", "dev"],
            cwd=["./robot_station/robot_station/frontend"],
            shell=True,
            output="screen",
        )
    )


def create_rosbridge_server_launch(ld: LaunchDescription) -> None:

    pck_dir = get_package_share_directory("rosbridge_server")

    xml_launch_path = os.path.join(pck_dir, "launch", "rosbridge_websocket_launch.xml")

    ld.add_action(
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(xml_launch_path),
        )
    )


def create_tello_control_station_launch(ld: LaunchDescription) -> None:
    ld.add_action(
        Node(
            package="tello_control_station",
            executable="control_station",
            output="screen",
        )
    )


def generate_launch_description():
    ld = LaunchDescription()

    pkg_dir = get_package_share_directory("robot_bringup")

    create_spot_driver_launch(ld, pkg_dir)
    create_robot_bt_launch(ld)
    create_rosbridge_server_launch(ld)
    create_video_interface_launch(ld)

    # ------------------
    # -    Plugins     -
    # ------------------

    create_hand_tracker_plugin_launch(ld)
    create_robot_agent_plugin_launch(ld)
    create_person_tracking_plugin_launch(ld)

    return ld
