import { useState, useEffect } from "react";
export function Carousel({ slidesImg }) {
    const [currentId, setCurrentId] = useState(1);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentId((s) => Math.floor(Math.random() * slidesImg.length));
        }, 3000);

        return () => {
            clearInterval(timer);
        };
    }, []);

    const imgs = slidesImg.map((element) => {
        return (
            <img
                src={element.src}
                className={
                    currentId === element.id
                        ? "carousel-item"
                        : "carousel-item-hidden"
                }
                alt={element.alt}
                key={element.id}
            />
        );
    });

    return <>{imgs}</>;
}
