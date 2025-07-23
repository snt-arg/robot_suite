import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def create_tello_driver_launch(ld: LaunchDescription) -> None:
    tello_driver_pkg_dir = get_package_share_directory("tello_driver")
    pkg_dir = get_package_share_directory("robot_bringup")
    params_file = os.path.join(pkg_dir, "config", "params.yaml")

    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(tello_driver_pkg_dir, "launch/tello_driver.launch.py")
            ),
            launch_arguments={
                "params_file": params_file,
                "use_compression": "true",
            }.items(),
        )
    )


def create_robot_bt_launch(ld: LaunchDescription) -> None:
    robot_bt_pkg_dir = get_package_share_directory("robot_bt")
    pkg_dir = get_package_share_directory("robot_bringup")
    params_file = os.path.join(pkg_dir, "config", "params.yaml")

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


def create_tello_control_station_launch(ld: LaunchDescription) -> None:
    ld.add_action(
        Node(
            package="tello_control_station",
            executable="control_station",
            output="screen",
        )
    )


def create_hand_tracker_plugin_launch(ld: LaunchDescription) -> None:
    pkg_dir = get_package_share_directory("robot_bringup")
    params_file = os.path.join(pkg_dir, "config", "params.yaml")
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
    params_file = os.path.join(pkg_dir, "config", "params.yaml")
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


def create_land_takeoff_plugin_launch(ld: LaunchDescription) -> None:
    pkg_dir = get_package_share_directory("robot_bringup")
    params_file = os.path.join(pkg_dir, "config", "params.yaml")
    ld.add_action(
        Node(
            package="object_following_plugin",
            executable="takeoff_node",
            parameters=[params_file],
        )
    )
    ld.add_action(
        Node(
            package="object_following_plugin",
            executable="land_node",
            parameters=[params_file],
        )
    )


def create_robot_agent_plugin_launch(ld: LaunchDescription) -> None:
    pkg_dir = get_package_share_directory("robot_bringup")
    params_file = os.path.join(pkg_dir, "config", "params.yaml")
    ld.add_action(
        Node(
            package="robot_agent",
            executable="robot_agent",
            parameters=[params_file],
            prefix="gnome-terminal --",
        )
    )


def generate_launch_description():
    ld = LaunchDescription()

    create_tello_driver_launch(ld)
    create_robot_bt_launch(ld)
    # create_tello_control_station_launch(ld)

    # ------------------
    # -    Plugins     -
    # ------------------

    create_hand_tracker_plugin_launch(ld)
    create_robot_agent_plugin_launch(ld)
    create_person_tracking_plugin_launch(ld)
    create_land_takeoff_plugin_launch(ld)

    return ld
