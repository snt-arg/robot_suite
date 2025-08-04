import React, { use, useEffect, useState } from "react";
import {
    telloRobotName,
    spotRobotName,
    go1RobotName,
    robotToRawDisplayMode,
} from "../../components/shared/utils/dataDicts";

import { VideoContainer } from "../../components/shared/VideoManager/VideoContainer";
import { SwitchPlugin } from "../../components/shared/pluginManager/SwitchPlugin";

export function InterfacePage() {
    const [displayMode, setDisplayMode] = useState("rawTello"); // Default display mode
    const [controlMode, setControlMode] = useState("keyboard"); // Default control mode
    const [robotName, setRobotName] = useState("tello");

    return (
        <>
            <div className="page-content-div-interface">
                <div className="header-div-interface">
                    <span>
                        <button
                            onClick={() => {
                                setRobotName((s) => telloRobotName);
                                setDisplayMode(robotToRawDisplayMode.tello);
                            }}
                        >
                            <img src="niceSPot.jpg" alt="Tello" />
                        </button>
                    </span>
                    <span>
                        <button
                            onClick={() => {
                                setRobotName((s) => spotRobotName);
                                setDisplayMode(robotToRawDisplayMode.spot);
                            }}
                        >
                            <img src="niceTello.jpg" alt="Spot" />
                        </button>
                    </span>
                    <span>
                        <button
                            onClick={() => {
                                setRobotName((s) => go1RobotName);
                                setDisplayMode(robotToRawDisplayMode.go1);
                            }}
                        >
                            <img src="nicego1.jpg" alt="Go1" />
                        </button>
                    </span>
                </div>
                <div className="left-div-interface">
                    <button
                        className="futuristic-button change-button change-display-button"
                        onClick={() => {
                            if (robotName.toLowerCase() === telloRobotName) {
                                setDisplayMode(robotToRawDisplayMode.tello);
                            } else if (
                                robotName.toLowerCase() === spotRobotName
                            ) {
                                setDisplayMode(robotToRawDisplayMode.spot);
                            } else if (
                                robotName.toLowerCase() === go1RobotName
                            ) {
                                setDisplayMode(robotToRawDisplayMode.go1);
                            }
                        }}
                    >
                        Raw Images
                    </button>
                    <button
                        className="futuristic-button change-button change-display-button"
                        onClick={() => setDisplayMode("annotatedHands")}
                    >
                        Annotated Hands
                    </button>
                    <button
                        className="futuristic-button change-button change-display-button"
                        onClick={() => setDisplayMode("allDetected")}
                    >
                        All Detected
                    </button>
                    <button
                        className="futuristic-button change-button change-display-button"
                        onClick={() => setDisplayMode("personTracked")}
                    >
                        Person Tracked
                    </button>
                    <button
                        className="futuristic-button change-button change-display-button"
                        onClick={() => setDisplayMode("personTrackedHands")}
                    >
                        Person tracked and Annotated Hands
                    </button>
                </div>

                <div className="video-div">
                    <VideoContainer displayMode={displayMode} />
                </div>

                <div className="right-div-interface">
                    <button
                        className="futuristic-button change-button change-plugin-button"
                        onClick={() => setControlMode("keyboard")}
                    >
                        Keyboard
                    </button>
                    <button
                        className="futuristic-button change-button change-plugin-button"
                        onClick={() => setControlMode("joystick")}
                    >
                        Joystick
                    </button>
                    <button
                        className="futuristic-button change-button change-plugin-button"
                        onClick={() => setControlMode("llmAgent")}
                    >
                        Natural language
                    </button>
                    <button
                        className="futuristic-button change-button change-plugin-button"
                        onClick={() => setControlMode("handGesture")}
                    >
                        Hand gestures
                    </button>
                </div>

                <div className="controls-div-interface">
                    <a href="/" className="futuristic-button">
                        <span>Go back</span>
                    </a>
                    <SwitchPlugin controlMode={controlMode} />
                </div>
            </div>
        </>
    );
}
