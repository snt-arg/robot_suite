import { useEffect, useState } from "react";

import { useRosSub } from "../utils/useRosSub";

import { RenderImage } from "../gui/RenderImage";

import { videoTypes } from "../utils/dataDicts";

const throttleRate = 100; // Adjust the throttle rate as needed

export function VideoContainer({ displayMode }) {
    const subscriber = useRosSub(
        videoTypes[displayMode].topic,
        videoTypes[displayMode].imgMsgType,
        throttleRate
    );
    const [imgSrc, setImgSrc] = useState("");

    useEffect(() => {
        if (subscriber) {
            let newImgSrc = String(JSON.parse(subscriber).data);
            setImgSrc((s) => newImgSrc);
        }
    }, [subscriber]);

    return (
        <div className="video-container">
            <RenderImage
                imgSrc={imgSrc}
                altText={videoTypes[displayMode].altText}
            />
        </div>
    );
}
