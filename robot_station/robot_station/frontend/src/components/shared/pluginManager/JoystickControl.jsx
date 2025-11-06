import Joystick from "rc-joystick";
import { useRosPub } from "../utils/useRosPub";
import { useEffect, useState, useRef } from "react";
import { commandInterpreter } from "../utils/utils";

/*On translation mode, */

const joystickToMovement = {
    translation: {
        right: "right",
        left: "left",
        top: "forward",
        bottom: "backward",
        righttop: "rightforward",
        topleft: "leftforward",
        leftbottom: "leftbackward",
        bottomright: "rightbackward",
        center: "stop",
    },
    rotation: {
        right: "rotateright",
        left: "rotateleft",
        top: "up",
        bottom: "down",
        center: "stop",
    },
};

export function JoystickControl({ topic, messageType }) {
    const timeStamp = useRef(Date.now());
    const publishingFrequency = 100; //millisecond

    const joystickBaseRadius = 75;
    const joystickControllerRadius = 30;

    const publish = useRosPub(topic, messageType);

    let twistMsg;

    useEffect(() => {
        //This allows to publish the same command if we keep the joystick at a certain position, for better joystick behavior.
        const continuousPublishing = setInterval(() => {
            if (Date.now() - timeStamp.current > publishingFrequency) {
                publish(twistMsg);
                timeStamp.current = Date.now();
            }
        }, publishingFrequency);

        return () => {
            clearInterval(continuousPublishing);
        };
    }, []);

    const joystickCommandHandler = (event, joystickType) => {
        //event.angle is also available.
        let joystickDirection = String(event.direction).toLowerCase();
        let joystickDistance = event.distance;

        console.log(
            "\nDirection: ",
            joystickDirection,
            "\nDistance: ",
            joystickDistance
        );

        const baseVelocity = (0.75 * joystickDistance) / joystickBaseRadius;
        const direction =
            joystickType === "translation"
                ? joystickToMovement.translation[joystickDirection]
                : joystickToMovement.rotation[joystickDirection];

        twistMsg = commandInterpreter(direction, baseVelocity);
        console.log("Twist:", twistMsg);

        publish(twistMsg);
    };

    return (
        <>
            {/*For the direction count, 1 means nine direction, and 0 means 5 directions */}

            <Joystick
                directionCount={1}
                baseRadius={joystickBaseRadius}
                controllerRadius={joystickControllerRadius}
                onChange={(event) =>
                    joystickCommandHandler(event, "translation")
                }
                className="joystick-left"
            />
            <Joystick
                directionCount={0}
                baseRadius={joystickBaseRadius}
                controllerRadius={joystickControllerRadius}
                onChange={(event) => joystickCommandHandler(event, "rotation")}
                className="joystick-right"
            />
        </>
    );
}
