import React, { use, useEffect, useState } from "react";
import { VideoContainer } from "../../components/shared/VideoManager/VideoContainer";
import { SwitchPlugin } from "../../components/shared/pluginManager/SwitchPlugin";
import { ChatArea } from "../../components/shared/pluginManager/ChatArea";
import { useChatHistory } from "../../components/shared/pluginManager/ChatArea";

/*
import { KeyboardControl } from "./KeyboardControl";
import { JoystickControl } from "./JoystickControl";
import { LlmControl } from "./LlmControl";*/

const telloRobotName = "tello";
const spotRobotName = "spot";
const go1RobotName = "go1";

export function InterfacePage() {
    const [displayMode, setDisplayMode] = useState("raw"); // Default display mode
    const [controlMode, setControlMode] = useState("keyboard"); // Default control mode
    const [msgList, updateReceivedMsg, updateSentMsg] = useChatHistory([]);
    const [userQuery, setUserQuery] = useState("");
    const [robotName, setRobotName] = useState("tello");



    return (
        <>
            <button className="change-display-button" onClick={() => setDisplayMode("raw")}>Raw Images</button>
            <button className="change-display-button" onClick={() => setDisplayMode("annotatedHands")}>Annotated Hands</button>
            <button className="change-display-button" onClick={() => setDisplayMode("allDetected")}>All Detected</button>
            <button className="change-display-button" onClick={() => setDisplayMode("personTracked")}>Person Tracked</button>
            <button className="change-display-button" onClick={() => setDisplayMode("personTrackedHands")}>Person tracked and Annotated Hands</button>
            <VideoContainer displayMode={displayMode} />

            <button className="change-plugin-button" onClick={() => setControlMode("keyboard")}>Keyboard</button>
            <button className="change-plugin-button" onClick={() => setControlMode("joystick")}>Joystick</button>
            <button className="change-plugin-button" onClick={() => setControlMode("llmAgent")}>Natural language</button>
            <button className="change-plugin-button" onClick={() => setControlMode("handGesture")}>Hand gestures</button>


            <SwitchPlugin controlMode={controlMode} />

            <button onClick={() => setRobotName(s => telloRobotName)}>Tello</button>
            <button onClick={() => setRobotName(s => spotRobotName)}>Spot</button>
            <button onClick={() => setRobotName(s => go1RobotName)}>Go1</button>

        </>
    );
}