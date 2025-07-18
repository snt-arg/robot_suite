import { useState, useEffect } from "react";
import { useRosPub } from "../utils/useRosPub";

import { commandInterpreter } from "../utils/utils";//interprets keyboard commands into velocity messages


const keyToMovement = {
    "w": "forward",
    "a": "left",
    "s": "backward",
    "d": "right",
    "arrowup": "up",
    "arrowdown": "down",
    "arrowleft": "rotateLeft",
    "arrowright": "rotateRight",
    " ": "stop"
};


export function KeyboardControl({ topic, messageType }) {
    const publish = useRosPub(topic, messageType);

    /* Just to test on Tello 1*/
    const publishTakeoff = useRosPub("/takeoff", "std_msgs/msg/Empty");
    const publishLand = useRosPub("/land", "std_msgs/msg/Empty");
    /* End just to test on Tello 1 */

    useEffect(() => {

        const keyboardCommandHandler = (event) => {

            let key = String(event.key).toLowerCase();

            /* Just to test on Tello 2*/
            if (key === "t") {
                publishTakeoff("Empty");
            }
            else if (key === "l") {
                publishLand("Empty");
            }

            /* End just to test on Tello 1 */

            else {
                let baseVelocity = 0.5;
                let direction = keyToMovement[key];

                publish(commandInterpreter(direction, baseVelocity));

            }


        }


        window.addEventListener("keydown", keyboardCommandHandler);

        return () => { window.removeEventListener("keydown", keyboardCommandHandler) };

    }, []);

    return <></>;
}