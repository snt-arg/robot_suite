import { use, useEffect, useState } from "react";
import { useRosPub } from "../utils/useRosPub";
import { KeyboardControl } from "./KeyboardControl";
import { JoystickControl } from "./JoystickControl";
import { LlmControl } from "./LlmControl";

const modeToMsg = {
    keyboard: { key: "m", className: "keyboard-control" },
    joystick: { key: "m", className: "joystick-control" },
    llmAgent: { key: "n", className: "llm-control" },
    handGesture: { key: "h", className: "hand-control" },
};

//Message types
const stringMessageType = "/std_msgs/msg/String";

//Topic names
const keyPressedTopic = "/key_pressed";

export function SwitchPlugin({
    controlMode = "keyboard",
    robotName = "tello",
}) {
    const publish = useRosPub(keyPressedTopic, stringMessageType);
    const [classNameVar, setClassName] = useState("");

    useEffect(() => {
        let msg = modeToMsg[controlMode].key;
        if (msg !== null && msg !== undefined) {
            setClassName((s) => modeToMsg[controlMode].className);
            publish(msg);
        } else {
            console.warn("Unknown control mode:", controlMode);
            console.warn("## Control mode UNCHANGED ##");
        }
    }, [controlMode]);

    return (
        <div className={classNameVar}>
            {controlMode === "keyboard" && (
                <KeyboardControl robotName={robotName} />
            )}

            {controlMode === "joystick" && (
                <JoystickControl robotName={robotName} />
            )}

            {controlMode === "llmAgent" && <LlmControl />}

            {controlMode === "handGesture" && (
                <img src="/assets/handGestureGuide.jpg" alt="Gesture guide" />
            )}
        </div>
    );
}
