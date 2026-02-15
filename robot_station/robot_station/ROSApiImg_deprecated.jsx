import ROSLIB from "roslib";
import { useState, useEffect, use } from 'react';
import { extractImgData, RenderImage } from "./frontend/src/components/shared/gui/RenderImage";


export function RosApiImg({ topic = "/camera/image_raw/compressed",
    messageType = "/sensor_msgs/msg/CompressedImage",
    throttleRate = 100,
    altText = "Raw images" }) {

    const [imgSrc, setImgSrc] = useState(" ");

    useEffect(() => {

        const ros = new ROSLIB.Ros({
            url: "ws://localhost:9090",
        });

        ros.on("connection", () => console.debug("Succesfully Connected to ROS"));
        ros.on("error", (err) => console.error("Error:", err));
        ros.on("close", () => console.debug("Closed the connection"));

        const imgListener = new ROSLIB.Topic({
            ros,
            name: topic,
            messageType: messageType, // Change this to the appropriate message type for your image topic
            throttle_rate: throttleRate, // Adjust the throttle rate as needed
        });

        imgListener.subscribe((msg) => {
            let imgData = extractImgData(msg)
            setImgSrc(s => imgData);
        });


        return () => {
            imgListener.unsubscribe();
            console.debug("Unsubscribed from image topic");
            ros.close();
            console.debug("Closed ROS connection");
        };

    }, [topic, messageType, throttleRate, altText]);

    return (
        <RenderImage imgSrc={imgSrc} altText={altText} />
    );
}