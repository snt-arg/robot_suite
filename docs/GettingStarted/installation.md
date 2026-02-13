# Installation

This section explains how to install the `robot_suite` directly on your machine (ie. not in Docker). To install with Docker, please refer to [Docker installation](../GettingStarted/docker.md).

## Prerequisites

The robot suite was only tested with :

- ROS2 Humble (on Ubuntu 22.04)
- ROS2 Jazzy (on Ubuntu 24.04)

!!! Danger "Important"

    If you want to install the `robot_suite` directly on your host (without Docker), make sure to create a virtual environment and perform the installation **within** the environment.

    Also make sure that ROS2 will look for packages inside your environment, to avoid missing dependencies errors.

    You can follow instructions in the next section to setup your virtual environment before installing the `robot_suite`. If your virtual environment is already set, feel free to jump to [Automatic Installation](#automatic-installation-recommended).

## Virtual environment setup

**Steps**

1. Create the virtual environment using `python3-venv`

    ```bash
    python -m venv <path_to_environment> --system-site-packages
    ```

    Make sure to replace `<path_to_environment>` with the actual path where you want your environment to be created. It is important to add the `--system-site-packages` flag for colcon to access required system packages.

1. Activate your environment
    ```bash
    source <path_to_environment>/bin/activate
    ```
1. If your virtual environment is located inside the `src` folder (ie `<your_workspace_name>/src`) , you have to make sure that colcon won't attempt to build it. You can do this with the following command:

    ```bash
    touch <path_to_environment>/COLCON_IGNORE
    ```

Now that you are done with setting the virtual environment up, you can proceed with the installation.

## Automatic Installation (Recommended) {#automatic-installation-recommended}

A script is provided to automatically install all dependencies and setup the workspace.
The robot type needs to be specified as an argument to the script. The available options are:

- `tello`: for the Tello drone
- `spot`: for the Spot robot
- `unitree_go1`: for the Unitree Go1 robot (Not yet supported)

```bash
sudo ./bootstrap.sh [robot]
```

!!! warning "Running the script"

    Make sure to run the script with `sudo`.

## Manual Installation

If you prefer to install the dependencies manually, you will first need to ensure
your robot driver is installed properly. Additionally, pip packages are required
which can be found in the `requirements.txt` file. You can install them using the following command:

```bash
pip install -r requirements.txt
```

For ros dependencies, you can use the following command:

```bash
rosdep install --from-paths . -r -y
```

!!! Note

    Here you can find the robot drivers:

    - Tello : [Tello ros2 driver](https://github.com/snt-arg/tello_ros2_driver.git) and [TelloPy](https://github.com/hanyazou/TelloPy.git )

    - Spot : [Spot ros2](https://github.com/bdaiinstitute/spot_ros2)

## Build

!!! Note

    The `bootstrap.sh` file automatically builds the `robot_suite` with colcon. So any later build after the script was successfully executed is a rebuild.

**Build Steps**

1. Sourcing the virtual environment
    ```bash
    source <path_to_environment>/bin/activate
    ```
1. Sourcing ROS2
    - Use this command if you have **never** built the `robot_suite` before.  
      Make sure to replace `<ros-distro>` with you ROS2 distribution (e.g humble, jazzy).

    ```bash
    source /opt/ros/<ros-distro>/setup.bash
    ```

    - If you have already built the suite (ie. `build` and `install` folders exist inside your workspace), use this command **instead**:

    ```bash
    source <path_to_robot_suite>/install/setup.bash
    ```

    Make sure to replace `<path_to_robot_suite>` with the actual path pointing to where you installed the suite.

1. Building the suite with colcon.

    ```bash
    cd <path_to_robot_suite>
    python3 -m colcon build --symlink-install
    ```
