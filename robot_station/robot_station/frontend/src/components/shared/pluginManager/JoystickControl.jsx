import Joystick from "rc-joystick";
import { useRosPub } from "../utils/useRosPub";
import { useEffect, useState, useRef } from "react";
import { commandInterpreter } from "../utils/utils";

/*On translation mode, */
const joystickModes = ["translation", "rotation"];

const joystickToMovement = {
    translation: {
        "right": "right",
        "left": "left",
        "top": "forward",
        "bottom": "backward",
        "righttop": "rightforward",
        "topleft": "leftforward",
        "leftbottom": "leftbackward",
        "bottomright": "rightbackward",
        "center": "stop",
    },
    rotation: {
        "right": "rotateright",
        "left": "rotateleft",
        "top": "up",
        "bottom": "down",
        "center": "stop",
    }
}

export function JoystickControl({ topic, messageType }) {
    const [joystickMode, setJoystickMode] = useState("translation");
    const [directionCount, setDirectionCount] = useState(1);

    const timeStamp = useRef(Date.now());
    const publishingFrequency = 100; //millisecond

    const joystickBaseRadius = 95;
    const joystickControllerRadius = 30;


    const publish = useRosPub(topic, messageType);

    let twistMsg;


    useEffect(() => {

        const activateRotation = (event) => {
            if (event.key === "r") {
                setJoystickMode(joystickModes[1]);
                setDirectionCount(s => 0)
            }
        }

        const deactivateRotation = (event) => {
            if (event.key === "r") {
                setJoystickMode(joystickModes[0]);
                setDirectionCount(s => 1)
            }
        }

        window.addEventListener("keydown", activateRotation);
        window.addEventListener("keyup", deactivateRotation);

        //This allows to publish the same command if we keep the joystick at a certain position, for better joystick behavior.
        const continuousPublishing = setInterval(() => {
            if (Date.now() - timeStamp.current > publishingFrequency) {
                publish(twistMsg);
                timeStamp.current = Date.now();
            }

        }, publishingFrequency);

        return () => {
            window.removeEventListener("keydown", activateRotation);
            window.removeEventListener("keyup", deactivateRotation);
            clearInterval(continuousPublishing);
        }
    }, []);


    const joystickCommandHandler = (event) => {
        //event.angle is also available.
        let joystickDirection = String(event.direction).toLowerCase();
        let joystickDistance = event.distance;

        console.log("\nDirection: ", joystickDirection, "\nDistance: ", joystickDistance);

        const baseVelocity = 0.75 * joystickDistance / (joystickBaseRadius);
        const direction = (joystickMode === "translation") ? joystickToMovement.translation[joystickDirection] : joystickToMovement.rotation[joystickDirection];

        twistMsg = commandInterpreter(direction, baseVelocity);
        console.log("Twist:", twistMsg);

        publish(twistMsg);

    }






    const clickHandle = () => {
        setJoystickMode((joystickMode === joystickModes[0]) ? joystickModes[1] : joystickModes[0]);
        setDirectionCount((directionCount === 0) ? setDirectionCount(s => 1) : setDirectionCount(s => 0));

    };




    return (
        <>
            {/*For the direction count, 1 means nine direction, and 0 means 5 directions */}
            <div>
                <Joystick directionCount={directionCount} baseRadius={joystickBaseRadius} controllerRadius={joystickControllerRadius} onChange={(event) => joystickCommandHandler(event)} />
                <button className={joystickMode === joystickModes[0] ? "buttonUnactive" : "buttonActive"}
                    onClick={() => clickHandle}>
                    R
                </button>
            </div>
        </>
    );
}



