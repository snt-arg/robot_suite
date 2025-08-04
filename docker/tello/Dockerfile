FROM ros:humble

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp 

# Install necessary and useful packages
RUN apt update && \
    apt install --no-install-recommends -y \
    ssh vim python3-pip python3-vcstool wget git iputils-ping\
    ros-$ROS_DISTRO-cv-bridge ros-$ROS_DISTRO-rmw-cyclonedds-cpp 

# Copy Robot Suite
COPY . /workspace/src/robot_suite


# Bring tello_ros2_driver pkg
RUN git clone https://github.com/snt-arg/tello_ros2_driver.git /workspace/src/tello_driver

# Install Tellopy
WORKDIR /tmp
RUN git clone https://github.com/hanyazou/TelloPy.git tellopy
WORKDIR /tmp/tellopy
RUN pip install .
WORKDIR /tmp
RUN rm -rf tellopy

# Install PIP libaries
WORKDIR /workspace/src/robot_suite
RUN pip install -r requirements.txt

# Run rosdep
WORKDIR /workspace
RUN rosdep update && \
    rosdep install --from-paths src --ignore-src -r -y

# Colcon build + source
WORKDIR /workspace
RUN . /opt/ros/humble/setup.sh && colcon build

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
