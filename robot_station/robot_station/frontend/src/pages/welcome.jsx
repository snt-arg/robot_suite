import { Carousel } from "../components/shared/gui/Carousel";
const slidesImg = [
    { src: "/assets/tello1-nobg.png", alt: "Tello", id: 0 },
    { src: "/assets/spot-nobg.png", alt: "Spot", id: 1 },
    { src: "/assets/tello2-nobg.png", alt: "Tello", id: 2 },
    { src: "/assets/go1-nobg.png", alt: "Go1", id: 3 },
];

export function WelcomePage() {
    return (
        <>
            <div className="page-content-div-welcome">
                <div className="left-div-welcome">
                    <div className="header-div-welcome">
                        <h1 className="main-title">Robot Station</h1>
                        <h2 className="second-level-title">
                            Robot suite video manager
                        </h2>
                    </div>
                    <a href="/interface" className="futuristic-button">
                        <span>Go to interface</span>
                    </a>

                    <a href="/info/Spot" className="futuristic-button">
                        <span>SPOT info</span>
                    </a>

                    <a href="/info/Tello" className="futuristic-button">
                        <span>Tello info</span>
                    </a>

                    <a href="/info/Go1" className="futuristic-button">
                        <span>Go1 info</span>
                    </a>
                </div>

                <div className="right-div-welcome">
                    <div className="rotating-shape"></div>
                    <div className="carousel">
                        <Carousel slidesImg={slidesImg} />
                    </div>
                </div>
            </div>
        </>
    );
}
