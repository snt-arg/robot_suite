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

    if [ "$IN_DOCKER" = "1" ]; then
        pip install . --break-system-packages
    else
        pip install .
    fi
    

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

# downloading piper models
download_piper_models() {
    local ROBOT_SUITE_DIR="$1"
    local MODEL_DIR="$ROBOT_SUITE_DIR/robot_agent/robot_agent/models"

    # Voice-specific info (directory + list of files)
    local FEMALE_DIR="$MODEL_DIR/female"
    local FEMALE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium"
    local FEMALE_FILES=(
        "en_US-amy-medium.onnx"
        "en_US-amy-medium.onnx.json"
    )

    local MALE_DIR="$MODEL_DIR/male"
    local MALE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/kusal/medium"
    local MALE_FILES=(
        "en_US-kusal-medium.onnx"
        "en_US-kusal-medium.onnx.json"
    )


    download_voice() {
        local dest_dir="$1"
        local base_url="$2"
        shift 2
        local files=("$@")

        mkdir -p "$dest_dir"

        for file in "${files[@]}"; do
            local url="$base_url/$file"
            local out="$dest_dir/$file"

            if [[ ! -f "$out" ]]; then
                echo "→ Downloading $file..."
                wget -q --show-progress "$url" -O "$out"
                if [[ $? -ne 0 ]]; then
                    print_error "Failed to download $file from $url. Download the file manually at $url. "
                fi
            else
                print_warning "$file already exists, skipping"
            fi
        done
    }
    
    print_info "Downloading Piper TTS models..."

    download_voice "$FEMALE_DIR" "$FEMALE_URL" "${FEMALE_FILES[@]}"

    download_voice "$MALE_DIR" "$MALE_URL" "${MALE_FILES[@]}"

}



function common_install(){
    # Ensure this script is run as root
    # run_as_root

    is_ros_installed
    source "/opt/ros/${ros_distro}/setup.sh" >> /dev/null

    mkdir -p drivers/

    # Check if rosdep is installed
    if [ "$(command -v rosdep)" == "" ]; then
        print_warning "rosdep is not installed. Installing it..."
        
        if [ "$IN_DOCKER" = "1" ]; then
            pip install rosdep --break-system-packages
        else
            pip install rosdep
        fi

        sudo rosdep init
        rosdep update
    else
        print_info "rosdep is already installed. Updating it..."
        rosdep update
    fi

    print_info "Installing dependencies for ROS packages"
    rosdep install --from-paths . -y

    apt remove python3-typing-extensions -y # to avoid conflicts with the pip version
    print_info "Installing dependencies for the project"
    if [ "$IN_DOCKER" = "1" ]; then
        pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision --break-system-packages
        pip install -r requirements.txt --break-system-packages 
    else
        pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision 
        pip install -r requirements.txt 
    fi

    download_piper_models "$(pwd)"
}

function tello_install(){
    print_info "Installing tellopy from source"
    install_tellopy

    print_info "Clonning tello_ros2_driver into drivers/"
    git clone https://github.com/snt-arg/tello_ros2_driver.git drivers/tello_ros2_driver
}

function spot_install(){
    print_info "Installing Spot driver 2"
    

    cd ./drivers
    
    # installing bosdyn_msgs and fetch the last version of proto2ros for jazzy support. this won't be necessary once bosdyn_msgs is updated to support jazzy.
    git clone --recurse-submodules https://github.com/bdaiinstitute/bosdyn_msgs.git
    git -C bosdyn_msgs checkout 209454f # need this version to be compatible with spot-cpp-sdk 5.1.0, while waiting for jazzy support in the official repo
    git -C bosdyn_msgs submodule update --init --recursive
    git -C bosdyn_msgs/proto2ros checkout 0cc2471 # need this to be compatible with bosdyn_msgs version above
    
    PIP_CONSTRAINT=./bosdyn_msgs/pip-constraint.txt rosdep install -i -y --from-path ../ --skip-keys "$(cat ./bosdyn_msgs/rosdep-skip.txt)"
    

    # ARCH=amd64  # or arm64
    # for url in $(cat ${ARCH}-dpkg.txt); do wget $url && sudo apt install -y ./$(basename $url); done
    # No need to do the above two lines anymore as we get the spot-cpp-sdk from our base image


    # installing spot_ros2
    git clone --recurse-submodules https://github.com/maeri18/spot_ros2.git
    cd ..
    
    
    ## Replacing the spot driver launch with our custom launch file.
    # rm /workspace/robot_suite/drivers/spot_ros2/spot_driver/launch/spot_driver.launch.py
    # mv /workspace/robot_suite/spot_driver.launch.py /workspace/robot_suite/drivers/spot_ros2/spot_driver/launch/
    
    chmod +x ./install_spot_ros2_jazzy.sh
    ./install_spot_ros2_jazzy.sh
    	
}

case "$1" in
    tello)
    
        common_install
        tello_install
        
        print_info "Building suite"
        python3 -m colcon build --symlink-install
        ;;
    spot)
        common_install
        spot_install
        
        print_info "Building suite"
        # python3 -m colcon build --symlink-install
        ;;
    unitree_go1)
        echo "Not yet supported,"
        exit 1
        common_install
        print_info "Building suite"
        python3 -m colcon build --symlink-install
        ;;
    *)
        echo "Unknown robot: $1."
        exit 1
        ;;
esac
