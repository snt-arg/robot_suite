FROM ros:humble

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp 

# Install necessary and useful packages
RUN apt update && \
    apt install --no-install-recommends -y \
    ssh vim python3-pip python3-vcstool wget git iputils-ping\
    ros-$ROS_DISTRO-cv-bridge ros-$ROS_DISTRO-rmw-cyclonedds-cpp python3-venv\
    ros-$ROS_DISTRO-controller-interface ros-$ROS_DISTRO-forward-command-controller\
    ros-$ROS_DISTRO-imu-sensor-broadcaster ros-$ROS_DISTRO-tf2-geometry-msgs\
    ros-$ROS_DISTRO-tf2-msgs ros-$ROS_DISTRO-tf2\
    ros-$ROS_DISTRO-geometry-msgs ros-$ROS_DISTRO-pluginlib\
    ros-$ROS_DISTRO-velodyne ros-$ROS_DISTRO-teleop-twist-keyboard \
    ros-$ROS_DISTRO-joint-state-publisher-gui ros-$ROS_DISTRO-tf-transformations \
    ros-$ROS_DISTRO-xacro ros-$ROS_DISTRO-depth-image-proc \ 
    ros-$ROS_DISTRO-bondcpp ros-$ROS_DISTRO-hardware-interface ros-$ROS_DISTRO-rclcpp\
    ros-$ROS_DISTRO-rclcpp-lifecycle ros-$ROS_DISTRO-realsense2-camera
    

COPY . /workspace/src/robot_suite

# Install PIP libaries
WORKDIR /workspace/src/robot_suite
RUN pip install -r requirements.txt

# Run rosdep
WORKDIR /workspace
RUN rosdep update && \
    rosdep install --from-paths src --ignore-src -r -y
    
    # Install Spot ROS2 driver
WORKDIR /workspace/src/robot_suite
RUN git clone https://github.com/bdaiinstitute/spot_ros2.git

WORKDIR /workspace/src/robot_suite/spot_ros2
RUN git submodule init && git submodule update
RUN ./install_spot_ros2.sh


# Colcon build + source
WORKDIR /workspace/src/
RUN . /opt/ros/humble/setup.sh #&& colcon build --symlink-install

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
#RUN echo "source /workspace/src/install/setup.bash" >> ~/.bashrc


# Build Entrypoint

RUN echo "#!/bin/bash" >> /entrypoint.sh \
    && echo "source /opt/ros/humble/setup.bash" >> /entrypoint.sh \
    #&& echo "source /workspace/src/install/setup.bash" >> /entrypoint.sh \
    && echo 'exec "$@"' >> /entrypoint.sh \
    && chmod a+x /entrypoint.sh

WORKDIR /workspace/src/robot_suite/

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
