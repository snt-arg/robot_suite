import React, { use, useEffect } from "react";
import { useRosPub } from "../utils/useRosPub";
import { KeyboardControl } from "./KeyboardControl";
import { JoystickControl } from "./JoystickControl";
import { LlmControl } from "./LlmControl";

const modeToMsg = {
    "keyboard": "m",
    "joystick": "m",
    "llmAgent": "n",
    "handGesture": "h",
}

//Message types
const stringMessageType = "/std_msgs/msg/String";
const velocityMessageType = "geometry_msgs/msg/Twist";

//Topic names
const keyPressedTopic = "/key_pressed";
const velocityTopic = "/cmd_vel";


export function SwitchPlugin({ controlMode = "keyboard" }) {
    const publish = useRosPub(keyPressedTopic, stringMessageType);


    useEffect(() => {

        let msg = modeToMsg[controlMode];
        if (msg !== null && msg !== undefined) {
            publish(msg);
        }
        else {
            console.warn("Unknown control mode:", controlMode);
            console.warn("## Control mode UNCHANGED ##");

        }

    }, [controlMode]);



    return (
        <div className="plugin-controls">
            {controlMode === "keyboard" && <KeyboardControl topic={velocityTopic} messageType={velocityMessageType} />}

            {controlMode === "joystick" && <JoystickControl topic={velocityTopic} messageType={velocityMessageType} />}

            {controlMode === "llmAgent" && <LlmControl />}

            {controlMode === "handGesture" && <img src="/assets/handGestureGuide.jpg" alt="Gesture guide" />}
        </div>
    );
}