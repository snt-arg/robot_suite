#!/bin/bash

ROS_DISTROS=("iron" "humble" "foxy")

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

    git clone --recurse-submodules https://github.com/bdaiinstitute/spot_ros2.git drivers/spot_ros2
    pushd drivers/spot_ros2

    sudo apt install -y wget

    ./install_spot_ros2.sh

    popd
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
