## On Host

This launch guide assumes that you succesfully installed and built the `robot_suite` directly on your machine (ie. not in Docker) by for example using the [installation guide](../GettingStarted/installation.md).

**Launch steps**

1.  Sourcing the virtual environment

    ```bash
    source <path_to_environment>/bin/activate
    ```

1.  Sourcing the suite

    ```bash
    source <path_to_workspace>/install/setup.bash
    ```

1.  Launching  
    You can either launch the whole `robot_suite`, or individual plugins (ie.[standalone mode](../Plugins/plugin_base.md/#for-developers)).
    - Whole suite

        ```bash
        ros2 launch robot_bringup <robot_platform>_launch.py
        ```

        (e.g. `ros2 launch robot_bringup tello_launch.py`)

    - Individual plugin in standalone mode

        ```bash
        ros2 run <plugin_name> <plugin_node_name> --ros-args -p standalone:=true
        ```

        (e.g. `ros2 run hand_gestures landmark_detector_node --ros-args -p standalone:=true`)

!!! Note

    - The available robot platforms are: **tello** and **spot**. More information at [Available Robot Platforms](../GettingStarted/docker.md/#available-platforms).

    - You can find the documentation on available plugins [here](../Plugins/about_plugins.md)

## With Docker

If you installed the suite using the [Docker installation guide](../GettingStarted/docker.md), and especially the [docker-compose](../GettingStarted/docker.md/#using-docker-compose-recommended) tutorial, the suite should be launched automatically after the container has started.

!!! Danger "Important"

    The `robot_agent` package needs to be launched in a seperate terminal even if you used the docker compose command.

    Make sure to launch the `robot_agent` in a separate terminal when needed.
    Use the commands:
    ```bash
    docker exec -ti <robot_platform>_suite bash
    ros2 run robot_agent robot_agent_node
    ```

    Don't forget to replace `robot_platform` with one of the [available robot platforms](../GettingStarted/docker.md/#available-platforms).

If you have a stopped container, follow these commands :

1.  Start the container

    On host, run

    ```bash
    docker start <container_name>
    ```

1.  Enter the container

    ```bash
    docker exec -ti  <container_name> bash
    ```

1.  Sourcing the suite

    Inside the container,

    ```bash
    source <path_to_workspace>/install/setup.bash
    ```

1.  Launching  
     You can either launch the **whole suite** or **plugins in standalone mode**. For either, run the corresponding command within the Docker container.
    - Whole suite

        ```bash
        ros2 launch robot_bringup <robot_platform>_launch.py
        ```

    - Individual plugin in standalone mode

        ```bash
        ros2 run <plugin_name> <plugin_node_name> --ros-args -p standalone:=true
        ```

    - Launch the `robot_agent` package if needed:
        - On Host

        ```bash
        docker exec -ti <robot_platform>_suite bash
        ```

        - Then within the container

        ```bash
        ros2 run robot_agent robot_agent_node

        ```

!!! Note "Example"

    If your container is named `tello_suite`, and you want to launch the whole suite, run

    - On Host:
    ```bash
    docker start tello_suite
    docker exec -ti tello_suite bash
    ```
    - Then inside the container:
    ```bash
    source /workspace/install/setup.bash
    ros2 launch robot_bringup tello_launch.py
    ```
    - (Optional) To also launch the `robot_agent`:

        On host
        ```bash
        docker exec -ti tello_suite bash
        ```
        Then within the container
        ```bash
        ros2 run robot_agent robot_agent_node
        ```
