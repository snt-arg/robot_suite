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
            <div className="page-content-div">
                <div className="left-div">
                    <div className="header-div">
                        <h1 className="main-title">Robot Station</h1>
                        <h2 className="second-level-title">
                            Robot suite video manager
                        </h2>
                    </div>
                    <button className="futuristic-button">
                        <a href="/interface">Go to interface</a>
                    </button>

                    <button className="futuristic-button">
                        <a href="/info/Spot">SPOT info</a>
                    </button>

                    <button className="futuristic-button">
                        <a href="/info/Tello">Tello info</a>
                    </button>

                    <button className="futuristic-button">
                        <a href="/info/Go1">Go1 info</a>
                    </button>
                </div>

                <div className="right-div">
                    <div className="rotating-shape"></div>
                    <div className="carousel">
                        <Carousel slidesImg={slidesImg} />
                    </div>
                </div>
            </div>
        </>
    );
}
