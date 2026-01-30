FROM ros:jazzy

# Set this in the compose file instead
# ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp 

# Install necessary and useful packages
RUN apt update && \
    apt install --no-install-recommends -y \
    ssh vim python3-pip python3-venv python3-vcstool wget git iputils-ping \
    ros-$ROS_DISTRO-cv-bridge ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
    ros-$ROS_DISTRO-image-transport ros-$ROS_DISTRO-rosbridge-suite \
    portaudio19-dev alsa-base alsa-utils

# Copy Robot Suite
COPY . /workspace/robot_suite

ARG IN_DOCKER=1
ENV IN_DOCKER=$IN_DOCKER
WORKDIR /workspace/robot_suite
SHELL ["/bin/bash", "-c"]
RUN ./bootstrap.sh tello

RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
RUN echo "source /workspace/robot_suite/install/setup.bash" >> ~/.bashrc


# Build Entrypoint

RUN echo "#!/bin/bash" >> /entrypoint.sh \
    && echo "source /opt/ros/jazzy/setup.bash" >> /entrypoint.sh \
    && echo "source /workspace/robot_suite/install/setup.bash" >> /entrypoint.sh \
    && echo 'exec "$@"' >> /entrypoint.sh \
    && chmod a+x /entrypoint.sh

WORKDIR /workspace/robot_suite
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
