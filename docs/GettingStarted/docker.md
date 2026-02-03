# 🐳 Docker

For this project, we are making use of [Docker Compose](https://docs.docker.com/compose/) to ease the build and start of containers.
The `docker-compose.yml` file is composed of services, where each service is
targeted for each robot platform.

This project uses **Docker Compose** to simplify building and running containers for different robot platforms.

The main configuration file is `docker-compose.yml`, which defines a separate **service** for each supported robot platform.

!!! note

    Currently, only the **Tello** and **Spot** robot platforms are supported.

## 🚀 Getting Started

!!! Danger "Important"

    If you want to use GUI applications inside Docker (e.g., visual tools like RViz), run the following command once before starting any containers:

    ```bash
    xhost +local:docker
    ```

### Using Docker Compose (Recommended)

!!! info

    Note that you will need to have `docker-compose` installed on your system.

    You can check with if it is installed with:

    ```bash
    docker-compose -v
    ```

    On Ubuntu, install it using:

    ```bash
    sudo apt install docker-compose
    ```

**Steps**:

1.  Open a terminal and navigate to the root directory of the project.

1.  Run the following command :
    ```bash
    docker compose up <robot_platform>_suite
    ```
    Don't forget to replace `<robot_platform>` with the desired platform !

**Available Platforms** <a id="available-platforms"></a>

Currently, dedicated Docker services (and corresponding containers) are available only for **tello** and **spot**.

- **tello**:
    ```bash
    docker compose up tello_suite
    ```
- **spot**:

    ```bash
    docker compose up spot_suite
    ```

    This should automatically start a container and launch the driver, plugins and behaviour tree for the corresponding robot platform.

### Manual Docker Usage (Advanced)

If you prefer not to use Docker Compose, you can build and run the containers manually.

Each robot platform has its own `Dockerfile` located at:  
`docker/<robot_platform>/Dockerfile`

!!! tip

    Do not forget to replace `<robot_platform>`  with one of the supported platforms:

    - tello
    - spot

**Steps**:

1. Go to the root of the project.

1. Build the Docker image:

```bash
docker build -t <robot_platform>_suite -f docker/<robot_platform>/Dockerfile .
```

- Run the container and launch the robot system (recommended):

```bash
docker run --rm -it \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /dev/dri:/dev/dri \
    -e DISPLAY=$DISPLAY \
    -e LIBGL_ALWAYS_SOFTWARE=1 \
    --device /dev/snd:/dev/snd \
    --net=host \
    <robot_platform>_suite \
    ros2 launch robot_bringup <robot_platform>_launch.py
```

- Or start the container with a terminal session:

```bash
docker run --rm -it \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /dev/dri:/dev/dri \
    -e DISPLAY=$DISPLAY \
    -e LIBGL_ALWAYS_SOFTWARE=1 \
    --device /dev/snd:/dev/snd \
    --net=host \
    <robot_platform>_suite \
```

!!! example "Example for Tello Platform"

    ```bash
    # Step 1: Build the Docker image
    docker build -t tello_suite -f docker/tello/Dockerfile .

    # Step 2: Enable GUI support
    xhost +local:docker

    # Step 3: Launch the system inside the container
    docker run --rm -it \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v /dev/dri:/dev/dri \
        -e DISPLAY=$DISPLAY \
        -e LIBGL_ALWAYS_SOFTWARE=1 \
        --device /dev/snd:/dev/snd \
        --net=host \
        tello_suite \
        ros2 launch robot_bringup tello_launch.py
    ```

!!!Note

    For the Spot suite, make sure to configure the configuration file of the spot_ros2 driver with the hostname, user name and password.
    Before running the driver.
