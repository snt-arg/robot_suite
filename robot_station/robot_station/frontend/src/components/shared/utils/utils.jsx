import ROSLIB from "roslib";

// Translation action map
const movement = {
    right: (twistMsg, baseVelocity) => {
        twistMsg.linear.y = -baseVelocity;
    },
    rightforward: (twistMsg, baseVelocity) => {
        twistMsg.linear.x = baseVelocity;
        twistMsg.linear.y = -baseVelocity;
    },
    forward: (twistMsg, baseVelocity) => {
        twistMsg.linear.x = baseVelocity;
    },
    leftforward: (twistMsg, baseVelocity) => {
        twistMsg.linear.x = baseVelocity;
        twistMsg.linear.y = baseVelocity;
    },
    left: (twistMsg, baseVelocity) => {
        twistMsg.linear.y = baseVelocity;
    },
    leftbackward: (twistMsg, baseVelocity) => {
        twistMsg.linear.x = -baseVelocity;
        twistMsg.linear.y = baseVelocity;
    },
    backward: (twistMsg, baseVelocity) => {
        twistMsg.linear.x = -baseVelocity;
    },
    rightbackward: (twistMsg, baseVelocity) => {
        twistMsg.linear.x = -baseVelocity;
        twistMsg.linear.y = -baseVelocity;
    },
    rotateright: (twistMsg, baseVelocity) => {
        twistMsg.angular.z = -baseVelocity;
    },
    rotateleft: (twistMsg, baseVelocity) => {
        twistMsg.angular.z = baseVelocity;
    },
    stop: (twistMsg) => {
        (twistMsg.linear.x = 0), (twistMsg.linear.y = 0);
        twistMsg.linear.z = 0;
        twistMsg.angular.x = 0;
        twistMsg.angular.y = 0;
        twistMsg.angular.z = 0;
    },
};

export function msgToRosMsg(msg, messageType) {
    let rosMsg = null;

    switch (messageType) {
        case "/std_msgs/msg/String":
            rosMsg = new ROSLIB.Message({
                data: String(msg), // Assuming msg is a ROS string
            });
            return rosMsg;
        case "geometry_msgs/msg/Twist":
            try {
                let msgObject = JSON.parse(msg); // Assuming msg is a JSON string

                if (
                    msgObject !== null &&
                    msgObject.linear !== undefined &&
                    msgObject.angular !== undefined
                ) {
                    let rosMsg = new ROSLIB.Message({
                        linear: {
                            x: msgObject.linear.x || 0,
                            y: msgObject.linear.y || 0,
                            z: msgObject.linear.z || 0,
                        },
                        angular: {
                            x: msgObject.angular.x || 0,
                            y: msgObject.angular.y || 0,
                            z: msgObject.angular.z || 0,
                        },
                    });
                    return rosMsg;
                }
            } catch (error) {
                console.error("Error creating Twist message:", error);
                return null;
            }
            break;
        case "std_msgs/msg/Empty":
            if (String(msg).toLowerCase() === "empty") {
                rosMsg = new ROSLIB.Message();
                return rosMsg;
            } else {
                console.warn(
                    "Attempted to publish a non-empty message: ",
                    msg,
                    "\nTo publish an empty message, use any case variant of 'empty'"
                );
                return null;
            }

        default:
            console.error("Unsupported message type:", messageType);
            return null;
    }
}

export function rosMsgToMsg(rosMsg, messageType) {
    let msg = null;

    switch (messageType) {
        case "/std_msgs/msg/String":
            msg = String(rosMsg.data);
            break;

        case "/sensor_msgs/msg/CompressedImage":
            msg = `data:image/jpeg;base64,${rosMsg.data}`;
            break;

        default:
            console.error("Unsupported message type:", messageType);
            return null;
    }
    return JSON.stringify({ data: msg, id: Date.now() });
}

export function commandInterpreter(direction, baseVelocity) {
    let twistMsg = {
        linear: { x: 0, y: 0, z: 0 },
        angular: { x: 0, y: 0, z: 0 },
    };

    if (direction in movement) {
        movement[direction](twistMsg, baseVelocity);
    } else {
        console.warn("Unknown direction:", direction);
        twistMsg = null; //if the direction is unknown, we send a null message that won't be published
    }

    return JSON.stringify(twistMsg);
}
