#!/bin/bash

ROS_DISTROS=("iron" "humble" "foxy" "jazzy")

# Colors
Color_Off='\033[0m'       # Text Reset
# Bold
BRed='\033[1;31m'         # Red
BBlue='\033[1;34m'       # Green
BYellow='\033[1;33m'      # Yellow

ros_distro=""

print_info(){
    echo -e "${BBlue}[INFO] -> ${Color_Off}${1}"
}

print_warning(){
    echo -e "${BYellow}[WARN] -> ${Color_Off}${1}"
}

print_error(){
    echo -e "${BRed}[ERROR] -> ${Color_Off}${1}"
}

function run_as_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root. [ sudo $0 ]"
        exit 1
    fi
}

is_ros_distro_installed(){
    local dist_name=$1
    local setup_file="/opt/ros/${dist_name}/setup.bash"

    if [ -f "$setup_file" ]; then
        return 1
    else
        return 0
    fi
}


is_ros_installed(){
    for distro in "${ROS_DISTROS[@]}";
    do
        is_ros_distro_installed "$distro"
        if [ $? == 1 ]; then
            ros_distro="$distro"
            break
        fi
    done

    if [ "$ros_distro" == "" ]; then
        print_error "No ROS distribution was found. Please Install it first!"
        exit 1
    fi
}

ask_user_input(){
    local message=$1
    local response=""

    printf "$message"
    read -r response
    response="${response:-Y}" # default is yes
    response="${response,,}" # tolower

    if [[ $response =~ ^(yes|y)$ ]]; then
        return 1
    elif [[ $response =~ ^(no|n)$ ]]; then
        return 0
    else
        print_error "Invalid input! Please enter 'yes' or 'no'!"
        exit 1
    fi
}

install_tellopy() {
    git clone https://github.com/hanyazou/TelloPy.git tellopy
    cd tellopy
    pip install .

    cd ..
    sudo rm -rf tellopy
}


# Check if Git is installed
if [ "$(command -v git)" == "" ]; then
    ask_user_input "git is not installed. Do you want to install it? [Y/n]"
    r=$?

    if [ $r == 1 ]; then
        sudo apt install -y git
    else
        print_error "Please install git first!"
        exit 1
    fi
fi


if [ "$(command -v pip)" == "" ]; then
    ask_user_input "pip is not installed. Do you want to install it? [Y/n]"
    r=$?

    if [ $r == 1 ]; then
        sudo apt install -y python3-pip
    else
        print_error "Please install pip first!"
        exit 1
    fi
fi


function common_install(){
    # Ensure this script is run as root
    # run_as_root

    is_ros_installed
    source "/opt/ros/${ros_distro}/setup.sh" >> /dev/null

    mkdir -p drivers/

    # Check if rosdep is installed
    if [ "$(command -v rosdep)" == "" ]; then
        print_warning "rosdep is not installed. Installing it..."

        pip install rosdep
        sudo rosdep init
        rosdep update
    else
        print_info "rosdep is already installed. Updating it..."
        rosdep update
    fi

    print_info "Installing dependencies for ROS packages"
    rosdep install --from-paths . -y

    print_info "Installing dependencies for the project"
    pip install -r requirements.txt
}

function tello_install(){
    print_info "Installing tellopy from source"
    install_tellopy

    print_info "Clonning tello_ros2_driver into drivers/"
    git clone https://github.com/snt-arg/tello_ros2_driver.git drivers/tello_ros2_driver
}

function spot_install(){
    print_info "Installing Spot driver 2"
    
    pip3 install --no-cache-dir -r ./requirements.txt --break-system-packages --ignore-installed
    
    mkdir -p drivers
    cd drivers
    
  
    # installing bosdyn_msgs
    git clone --recurse-submodules https://github.com/bdaiinstitute/bosdyn_msgs.git
    PIP_CONSTRAINT=./bosdyn_msgs/pip-constraint.txt rosdep install -i -y --from-path ../ --skip-keys "$(cat ./bosdyn_msgs/rosdep-skip.txt)"
    
    cd bosdyn_msgs
    ARCH=amd64  # or arm64
    #for url in $(cat ${ARCH}-dpkg.txt); do wget $url && sudo apt install -y ./$(basename $url); done
    
    # Changing the generate.py file in proto2ros with another one where importlib.resources.path is not used as an os.PathLike object
    rm /workspace/src/robot_suite/drivers/bosdyn_msgs/proto2ros/proto2ros/proto2ros/cli/generate.py
    mv /workspace/src/robot_suite/files_for_replacing/generate.py /workspace/src/robot_suite/drivers/bosdyn_msgs/proto2ros/proto2ros/proto2ros/cli/
    
    
    cd /
    
    # installing spot_cpp_sdk 
    mkdir spot_sdk_install
    cd spot_sdk_install
    
    git clone https://github.com/microsoft/vcpkg
    cd vcpkg
    
    git checkout 3b213864579b6fa686e38715508f7cd41a50900f
    
    ./bootstrap-vcpkg.sh
    ./vcpkg install grpc:x64-linux
    ./vcpkg install eigen3:x64-linux
    ./vcpkg install cli11:x64-linux
    cd ..
    
    
    git clone https://github.com/boston-dynamics/spot-cpp-sdk.git
    
    
    # The original signal_schema_key.h misses an import (cstdint) following new updates on C++
    # So we replace their file with a similar file, that import added
   
    rm /spot_sdk_install/spot-cpp-sdk/cpp/bosdyn/client/data_buffer/signal_schema_key.h
    mv /workspace/src/robot_suite/files_for_replacing/signal_schema_key.h /spot_sdk_install/spot-cpp-sdk/cpp/bosdyn/client/data_buffer
    
    cd spot-cpp-sdk/
  
    cd cpp/
 
    mkdir build
    cd build
    cmake ../ -DCMAKE_TOOLCHAIN_FILE=/spot_sdk_install/vcpkg/scripts/buildsystems/vcpkg.cmake -DCMAKE_INSTALL_PREFIX=/spot_sdk_install/spot-cpp-sdk -DCMAKE_FIND_PACKAGE_PREFER_CONFIG=TRUE
    
    make -j6 install package
    
    cd /workspace/src/robot_suite/drivers
    	
    # installing spot_ros2
    git clone https://github.com/bdaiinstitute/spot_ros2.git
    cd spot_ros2 
    git submodule init
    git submodule update
    
    # Replacing files with import errors with correct files. 
    ## Three files had an import error on cv_bridge (wrong extension, .h when it should be .hpp). 
    rm /workspace/src/robot_suite/drivers/spot_ros2/spot_driver/src/image_stitcher/image_stitcher.cpp /workspace/src/robot_suite/drivers/spot_ros2/spot_driver/src/conversions/decompress_images.cpp /workspace/src/robot_suite/drivers/spot_ros2/spot_driver/src/api/default_image_client.cpp
    
    mv /workspace/src/robot_suite/files_for_replacing/image_stitcher.cpp /workspace/src/robot_suite/drivers/spot_ros2/spot_driver/src/image_stitcher/
    
    mv /workspace/src/robot_suite/files_for_replacing/decompress_images.cpp /workspace/src/robot_suite/drivers/spot_ros2/spot_driver/src/conversions/
    
    mv /workspace/src/robot_suite/files_for_replacing/default_image_client.cpp /workspace/src/robot_suite/drivers/spot_ros2/spot_driver/src/api/
    
    ## One file had an import that is no more necessary (#include <gmock/gmock-generated-matchers.h> when new versions of gmock do not require this)
    
    rm /workspace/src/robot_suite/drivers/spot_ros2/spot_driver/test/include/spot_driver/matchers.hpp
    
    mv /workspace/src/robot_suite/files_for_replacing/matchers.hpp /workspace/src/robot_suite/drivers/spot_ros2/spot_driver/test/include/spot_driver/
    
    ## Replacing the spot driver launch with our custom launch file.
    rm /workspace/src/robot_suite/drivers/spot_ros2/spot_driver/launch/spot_driver.launch.py
    mv /workspace/src/robot_suite/files_for_replacing/spot_driver.launch.py /workspace/src/robot_suite/drivers/spot_ros2/spot_driver/launch/
    
    
    cd ../..
    
    chmod +x ./install_spot_ros2_jazzy.sh
    ./install_spot_ros2_jazzy.sh
    
    cd ../..
    	
   
}

case "$1" in
    tello)
        tello_install
        common_install

        print_info "Building suite"
        colcon build --symlink-install
        ;;
    spot)
        spot_install
        common_install

        print_info "Building suite"
        colcon build --symlink-install
        ;;
    unitree_go1)
        echo "Not yet supported,"
        exit 1
        common_install
        print_info "Building suite"
        colcon build --symlink-install
        ;;
    *)
        echo "Unknown robot: $1."
        exit 1
        ;;
esac
