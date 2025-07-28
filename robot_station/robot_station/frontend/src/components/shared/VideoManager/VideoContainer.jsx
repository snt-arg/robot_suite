import { useEffect, useState } from "react";

import { useRosSub } from "../utils/useRosSub";

import { RenderImage } from "../gui/RenderImage";

/*Image types*/
const rawImageType = "/sensor_msgs/msg/Image"; // Adjust this to the correct message type if needed

const compressedImageType = "/sensor_msgs/msg/CompressedImage"; // Adjust this to the correct message type if needed


/*Topic names*/
const topicRawCompressed = "/camera/image_raw/compressed"; // Default topic for compressed images
const topicRaw = "/camera/image_raw"; // Default topic for raw images
const topicAnnotatedHands = "/hand/annotated/image/compressed";
const topicAllDetected = "/camera/all_detected/compressed";
const topicPersonTracked = "/camera/person_tracked/compressed";
const topicPersonTrackedHands = "/camera/hands/person_tracked/compressed";

const throttleRate = 100; // Adjust the throttle rate as needed 

const videoTypes = {
    "raw": {
        topic: topicRawCompressed,
        imgMsgType: compressedImageType,
        alt_text: "Raw Images"
    },
    "annotatedHands": {
        topic: topicAnnotatedHands,
        imgMsgType: compressedImageType,
        altText: "Annotated Hands"

    },
    "allDetected": {
        topic: topicAllDetected,
        imgMsgType: compressedImageType,
        altText: "All Detected"

    },
    "personTracked": {
        topic: topicPersonTracked,
        imgMsgType: compressedImageType,
        altText: "Person Tracked"

    },
    "personTrackedHands": {
        topic: topicPersonTrackedHands,
        imgMsgType: compressedImageType,
        altText: "Person Tracked Hands"

    },
}
export function VideoContainer({ displayMode }) {
    const subscriber = useRosSub(videoTypes[displayMode].topic, videoTypes[displayMode].imgMsgType, throttleRate);
    const [imgSrc, setImgSrc] = useState("");

    useEffect(() => {

        if (subscriber) {
            let newImgSrc = String(JSON.parse(subscriber).data);
            setImgSrc(s => newImgSrc);
        }

    }, [subscriber]);

    return (
        <div className="video-container">
            <RenderImage imgSrc={imgSrc} altText={videoTypes[displayMode].altText} />
        </div>
    );
}