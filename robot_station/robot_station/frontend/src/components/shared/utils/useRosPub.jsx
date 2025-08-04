import ROSLIB from "roslib";
import { useEffect, useRef } from 'react';
import { msgToRosMsg } from "./utils";

export function useRosPub(topic, messageType) {
    const publisher = useRef(null);

    useEffect(() => {
        const ros = new ROSLIB.Ros({
            url: "ws://localhost:9090",
        });

        ros.on("connection", () => console.debug("Succesfully Connected to ROS"));
        ros.on("error", (err) => console.error("Error:", err));
        ros.on("close", () => console.debug("Closed the connection"));


        publisher.current = new ROSLIB.Topic({
            ros,
            name: topic,
            messageType: messageType,
        });

        publisher.current.advertise();

        return () => {
            publisher.current.unadvertise();
            console.debug("Unadvertised publisher from topic:", topic);
            ros.close();
            console.debug("Closed ROS connection");

        };

    }, [topic, messageType]);

    const publish = (msg) => {
        if (publisher.current === null || publisher.current == undefined) {
            console.error("Publisher not yet ready");

        }

        else {
            const message = msgToRosMsg(msg, messageType);
            if (message === null || message === undefined) {
                console.error("Failed to create ROS message from input:", msg);
            }
            else {
                publisher.current.publish(message);
                console.log("Published message:", message, "\nto topic:", topic);
            }
        }
    }


    return publish;

}
