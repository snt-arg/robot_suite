ARCH="amd64"
SDK_VERSION="5.0.1"
MSG_VERSION="${SDK_VERSION}"
HELP=$'--arm64: Installs ARM64 version'
REQUIREMENTS_FILE=./spot_requirements.txt

while true; do
  case "$1" in
    --arm64 | --aarch64 ) ARCH="arm64"; shift ;;
    -h | --help ) echo "$HELP"; exit 0;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done

sudo apt-get update && sudo apt-get install -y python3-rosdep python3-pip wget

if test -f "$REQUIREMENTS_FILE"; then
    if [ "$IN_DOCKER" = "1" ]; then
        sudo pip3 install --no-cache-dir -r $REQUIREMENTS_FILE --break-system-packages
    else
        sudo pip3 install --no-cache-dir -r $REQUIREMENTS_FILE 
    fi
    
else
    echo "ERROR: $REQUIREMENTS_FILE not found. Please initialize spot_wrapper with: git submodule init --update"
    exit 1
fi

# Install ROS dependencies
#NOTE: Initialize only if a sources list definition doesn't exist yet - avoids the rosdep error message
if ! [[ $(ls /etc/ros/rosdep/sources.list.d/*default.list 2> /dev/null) ]]; then
  sudo rosdep init
fi
source /opt/ros/jazzy/setup.bash && rosdep update && rosdep install --from-paths ./ --ignore-src -y -r --rosdistro=jazzy

# Install Qt5UiTools
sudo apt-get install -y qttools5-dev

# Install the dist-utils
sudo apt-get install -y python3-distutils
sudo apt-get install -y python3-apt
# sudo pip3 install --no-cache-dir --force-reinstall -v "setuptools==59.6.0"

# Install bosdyn_msgs - automatic conversions of BD protobufs to ROS messages

# Install spot-cpp-sdk
sudo dpkg -i /spot_sdk_install/spot-cpp-sdk/cpp/build/spot-cpp-sdk_5.0.1.2_amd64.deb
