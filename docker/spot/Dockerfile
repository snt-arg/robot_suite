FROM ros:humble

# Set this in the compose file instead
# ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp 

# Install necessary and useful packages
RUN apt update && \
    apt install --no-install-recommends -y \
    ssh vim python3-pip python3-vcstool wget git iputils-ping \
    ros-$ROS_DISTRO-cv-bridge ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
    ros-$ROS_DISTRO-image-transport

# Copy Robot Suite
COPY . /workspace/src/robot_suite

WORKDIR /workspace/src/robot_suite
SHELL ["/bin/bash", "-c"]
RUN ./bootstrap.sh spot

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
RUN echo "source /workspace/install/setup.bash" >> ~/.bashrc


# Build Entrypoint

RUN echo "#!/bin/bash" >> /entrypoint.sh \
    && echo "source /opt/ros/humble/setup.bash" >> /entrypoint.sh \
    && echo "source /workspace/install/setup.bash" >> /entrypoint.sh \
    && echo 'exec "$@"' >> /entrypoint.sh \
    && chmod a+x /entrypoint.sh

WORKDIR /workspace/src/robot_suite

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]

