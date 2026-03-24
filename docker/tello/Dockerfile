FROM ros:humble

# Set this in the compose file instead
# ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp 

# Install necessary and useful packages
RUN apt update && \
    apt install --no-install-recommends -y \
    ssh vim python3-pip python3-vcstool wget git iputils-ping \
    ros-$ROS_DISTRO-cv-bridge ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
    ros-$ROS_DISTRO-image-transport ros-$ROS_DISTRO-rosbridge-server \
    portaudio19-dev python3-dev 
    
    # Note: portaudio-dev and python3-dev are For PyAudio

# Copy Robot Suite
COPY . /workspace/robot_suite

WORKDIR /workspace/robot_suite
SHELL ["/bin/bash", "-c"]
RUN ./bootstrap.sh tello

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
RUN echo "source /workspace/robot_suite/install/setup.bash" >> ~/.bashrc


# Build Entrypoint

RUN echo "#!/bin/bash" >> /entrypoint.sh \
    && echo "source /opt/ros/humble/setup.bash" >> /entrypoint.sh \
    && echo "source /workspace/robot_suite/install/setup.bash" >> /entrypoint.sh \
    && echo 'exec "$@"' >> /entrypoint.sh \
    && chmod a+x /entrypoint.sh

WORKDIR /workspace/robot_suite

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
