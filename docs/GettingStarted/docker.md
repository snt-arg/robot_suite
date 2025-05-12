# 🐳 Docker

For this project, we are making use of Docker Compose to ease the build and start of containers.
The `docker-compose.yml` file is/will be composed of services, where each service is
targeted for each robot platform.

This project uses **Docker Compose** to simplify building and running containers for different robot platforms.

The main configuration file is `docker-compose.yml`, which defines a separate **service** for each supported robot platform.

!!! note

    Currently, only the **Tello** robot platform is supported.

## 🚀 Getting Started

!!! Danger "Important"

    If you want to use GUI applications inside Docker (e.g., visual tools like RViz), run the following command once before starting any containers:

    ```bash
    xhost +local:docker
    ```

### Using Docker Compose (Recommended)

!!! info

    Note that you will need to have `docker-compose` installed on your system.
    You can check if it is installed by running `docker-compose -v`. On ubuntu,
    you can install it using `sudo apt install docker-compose`

    Make sure you have docker-compose installed.
    You can check with:

    ```bash
    docker-compose -v
    ```

    On Ubuntu, install it using:

    ```bash
    sudo apt install docker-compose
    ```

**Steps**:

1. Open a terminal and navigate to the root directory of the project.

1. Run the following command (replace <robot_platform> with the desired platform):
   docker compose up <robot_platform>\_suite

**Available Platforms**

- **tello**:
    ```bash
    docker compose up tello_suite
    ```

### Manual Docker Usage (Advanced)

If you prefer not to use Docker Compose, you can build and run the containers manually.

Each robot platform has its own `Dockerfile` located at: `docker/<robot_platform>/Dockerfile`

!!! tip

    Replace <robot_platform> with one of the supported platforms:

    - tello

**Steps**:

- Go to the root of the project.

- Build the Docker image:

```bash
docker build -t <robot_platform>_suite -f docker/<robot_platform>/Dockerfile .
```

- Run the container and launch the robot system (recommended):

```bash
docker run --rm -it \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=$DISPLAY \
    --net=host \
    <robot_platform>_suite \
    ros2 launch <robot_package> system_launch.py
```

- Or start the container with a terminal session:

```bash
docker run --rm -it \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=$DISPLAY \
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
        -e DISPLAY=$DISPLAY \
        --net=host \
        tello_suite \
        ros2 launch tello_bringup system_launch.py
    ```
