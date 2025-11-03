FROM ros:jazzy

# Set this in the compose file instead
# ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp 

# Install necessary and useful packages
RUN apt update && \
    apt install --no-install-recommends -y \
    file ssh vim python3-pip python3-vcstool wget git iputils-ping clang-tidy \
    build-essential git g++ pkg-config curl tar zip unzip zlib1g-dev libssl-dev \
    cmake python3-colcon-common-extensions ros-dev-tools \
    libprotobuf-dev libgrpc++1.51t64 libprotobuf32t64 libpython3.12 \
    libcli11-dev libgrpc++-dev libprotoc-dev python3-networkx python3-inflection libboost-python-dev\
    python3-multipledispatch protobuf-compiler \
    ros-$ROS_DISTRO-image-transport ros-$ROS_DISTRO-fastcdr\
    ros-$ROS_DISTRO-rosbridge-suite ros-$ROS_DISTRO-geometry-msgs ros-$ROS_DISTRO-cv-bridge-dbgsym\ 
    ros-$ROS_DISTRO-rosidl-default-runtime ros-$ROS_DISTRO-ament-cmake-mypy \
    ros-$ROS_DISTRO-builtin-interfaces ros-$ROS_DISTRO-rclcpp ros-$ROS_DISTRO-teleop-twist-keyboard\
    ros-$ROS_DISTRO-rclpy ros-$ROS_DISTRO-rosidl-adapter ros-$ROS_DISTRO-bondcpp-dbgsym  \
    ros-$ROS_DISTRO-rosidl-default-generators ros-$ROS_DISTRO-std-msgs &&\
    rm -rf /var/lib/apt/lists/*


# Copy Robot Suite
COPY . /workspace/src/robot_suite

WORKDIR /workspace/src/robot_suite
SHELL ["/bin/bash", "-c"]
RUN ./bootstrap.sh spot

RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
RUN echo "source /workspace/install/setup.bash" >> ~/.bashrc


# Build Entrypoint

RUN echo "#!/bin/bash" >> /entrypoint.sh \
    && echo "source /opt/ros/jazzy/setup.bash" >> /entrypoint.sh \
    && echo "source /workspace/install/setup.bash" >> /entrypoint.sh \
    && echo 'exec "$@"' >> /entrypoint.sh \
    && chmod a+x /entrypoint.sh

WORKDIR /workspace/src/robot_suite

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]

