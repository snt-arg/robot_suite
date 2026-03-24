import { useEffect, useState } from "react";

import { useRosSub } from "../utils/useRosSub";

import { RenderImage } from "../gui/RenderImage";

import { videoTypes, displayModes } from "../utils/dataDicts";

const throttleRate = 100; // Adjust the throttle rate as needed

export function VideoContainer({ displayMode, robotName }) {
    let topic = null;
    let messageType = null;
    let altText = null;

    if (displayMode === displayModes.raw) {
        topic = videoTypes[displayMode][robotName].topic;
        messageType = videoTypes[displayMode][robotName].imgMsgType;
        altText = videoTypes[displayMode][robotName].altText;
    } else {
        topic = videoTypes[displayMode].topic;
        messageType = videoTypes[displayMode].imgMsgType;
        altText = videoTypes[displayMode].altText;
    }

    const subscriber = useRosSub(topic, messageType, throttleRate);
    const [imgSrc, setImgSrc] = useState("");

    useEffect(() => {
        if (subscriber) {
            let newImgSrc = String(JSON.parse(subscriber).data);
            setImgSrc((s) => newImgSrc);
        }
    }, [subscriber]);

    return (
        <div className="video-container">
            <RenderImage imgSrc={imgSrc} altText={altText} />
        </div>
    );
}
