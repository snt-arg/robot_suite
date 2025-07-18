import ROSLIB from "roslib";
import { useState, useEffect, useRef } from 'react';
import { rosMsgToMsg } from "./utils";


export function useRosSub(topic,
    messageType,
    throttleRate = 100) {
    const [msgState, setMsgState] = useState(null);
    const listener = useRef(null);


    useEffect(() => {

        const ros = new ROSLIB.Ros({
            url: "ws://localhost:9090",
        });

        ros.on("connection", () => console.debug("Succesfully Connected to ROS"));
        ros.on("error", (err) => console.error("Error:", err));
        ros.on("close", () => console.debug("Closed the connection"));

        listener.current = new ROSLIB.Topic({
            ros,
            name: topic,
            messageType: messageType, // Change this to the appropriate message type for your image topic
            throttle_rate: throttleRate, // Adjust the throttle rate as needed
        });

        listener.current.subscribe((rosMsg) => {
            let msg = rosMsgToMsg(rosMsg, messageType);
            setMsgState(s => msg);

            console.debug("received message: ", rosMsg, "and coverted it to: ", msg);

        });

        return () => {
            listener.current.unsubscribe();
            console.debug("Unsubscribed from topic: ", topic);
            ros.close();
            console.debug("Closed ROS connection");
        };

    }, [topic, messageType, throttleRate]);



    return msgState;
}