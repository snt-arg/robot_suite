import { useEffect } from "react";
import { useRosPub } from "../utils/useRosPub";
import { sharedkeyToMovement } from "../utils/dataDicts"; // shared key to movement mapping
import { commandInterpreter } from "../utils/utils"; //interprets keyboard commands into velocity messages
import { robotToVelocityTopicAndMessageType } from "../utils/dataDicts";

import { telloCommandInterpreter } from "../../tello/telloCommandInterpreter";
import { spotCommandInterpreter } from "../../spot/spotCommandInterpreter";
import { go1CommandInterpreter } from "../../go1/go1CommandInterpreter";

const robotToSpecificInterpreter = {
    tello: telloCommandInterpreter,
    spot: spotCommandInterpreter,
    go1: go1CommandInterpreter,
};

export function KeyboardControl({ robotName }) {
    const { topic, messageType } =
        robotToVelocityTopicAndMessageType[robotName.toLowerCase()];

    const publish = useRosPub(topic, messageType);

    let baseVelocity = 0.5;

    useEffect(() => {
        const keyboardCommandHandler = (event) => {
            let key = String(event.key).toLowerCase();

            if (key in sharedkeyToMovement) {
                let direction = sharedkeyToMovement[key];
                let command = commandInterpreter(direction, baseVelocity);
                if (command !== null && command !== undefined) {
                    publish(command);
                }
            } else {
                robotToSpecificInterpreter[robotName](key, baseVelocity);
            }
        };

        window.addEventListener("keydown", keyboardCommandHandler);

        return () => {
            window.removeEventListener("keydown", keyboardCommandHandler);
        };
    }, []);

    return <></>;
}
