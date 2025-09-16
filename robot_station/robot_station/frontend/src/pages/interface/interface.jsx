import React, { use, useEffect, useState } from "react";
import {
    robotNames,
    pluginNames,
    displayModes,
} from "../../components/shared/utils/dataDicts";

import { VideoContainer } from "../../components/shared/VideoManager/VideoContainer";
import { SwitchPlugin } from "../../components/shared/pluginManager/SwitchPlugin";

export function InterfacePage() {
    const [displayMode, setDisplayMode] = useState(displayModes.raw); // Default display mode
    const [controlMode, setControlMode] = useState(pluginNames.keyboard); // Default control mode
    const [robotName, setRobotName] = useState(robotNames.Tello);

    return (
        <>
            <div className="page-content-div-interface">
                <div className="header-div-interface">
                    <span>
                        <button
                            onClick={() => {
                                setRobotName((s) => robotNames.Tello);
                            }}
                        >
                            <img src="niceSPot.jpg" alt="Tello" />
                        </button>
                    </span>
                    <span>
                        <button
                            onClick={() => {
                                setRobotName((s) => robotNames.Spot);
                            }}
                        >
                            <img src="niceTello.jpg" alt="Spot" />
                        </button>
                    </span>
                    <span>
                        <button
                            onClick={() => {
                                setRobotName((s) => robotNames.Go1);
                            }}
                        >
                            <img src="nicego1.jpg" alt="Go1" />
                        </button>
                    </span>
                </div>
                <div className="left-div-interface">
                    <button
                        className="futuristic-button change-button change-display-button"
                        onClick={() => setDisplayMode(displayModes.raw)}
                    >
                        Raw Images
                    </button>
                    <button
                        className="futuristic-button change-button change-display-button"
                        onClick={() =>
                            setDisplayMode(displayModes.annotatedHands)
                        }
                    >
                        Annotated Hands
                    </button>
                    <button
                        className="futuristic-button change-button change-display-button"
                        onClick={() => setDisplayMode(displayModes.allDetected)}
                    >
                        All Detected
                    </button>
                    <button
                        className="futuristic-button change-button change-display-button"
                        onClick={() =>
                            setDisplayMode(displayModes.personTracked)
                        }
                    >
                        Person Tracked
                    </button>
                    <button
                        className="futuristic-button change-button change-display-button"
                        onClick={() =>
                            setDisplayMode(displayModes.personTrackedHands)
                        }
                    >
                        Person tracked and Annotated Hands
                    </button>
                </div>

                <div className="video-div">
                    <VideoContainer
                        displayMode={displayMode}
                        robotName={robotName}
                    />
                </div>

                <div className="right-div-interface">
                    <button
                        className="futuristic-button change-button change-plugin-button"
                        onClick={() => setControlMode(pluginNames.keyboard)}
                    >
                        Keyboard
                    </button>
                    <button
                        className="futuristic-button change-button change-plugin-button"
                        onClick={() => setControlMode(pluginNames.joystick)}
                    >
                        Joystick
                    </button>
                    <button
                        className="futuristic-button change-button change-plugin-button"
                        onClick={() => setControlMode(pluginNames.llmAgent)}
                    >
                        Natural language
                    </button>
                    <button
                        className="futuristic-button change-button change-plugin-button"
                        onClick={() => setControlMode(pluginNames.handGesture)}
                    >
                        Hand gestures
                    </button>
                </div>

                <div className="controls-div-interface">
                    <a href="/" className="futuristic-button">
                        <span>Go back</span>
                    </a>
                    <SwitchPlugin
                        controlMode={controlMode}
                        robotName={robotName}
                    />
                </div>
            </div>
        </>
    );
}
