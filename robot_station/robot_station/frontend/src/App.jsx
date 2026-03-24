import { BrowserRouter, Routes, Route } from "react-router-dom";

import { InterfacePage } from "./pages/interface/interface";
import { WelcomePage } from "./pages/welcome";
import { SpotInfo } from "./pages/information/spotInfo";
import { TelloInfo } from "./pages/information/telloInfo";
import { Go1Info } from "./pages/information/unitree";

export default function App() {
    return (
        <>
            <BrowserRouter>
                <Routes>
                    <Route path="/">
                        <Route path="/" element={<WelcomePage />} />
                        <Route path="info/Spot" element={<SpotInfo />} />
                        <Route path="info/Tello" element={<TelloInfo />} />
                        <Route path="info/Go1" element={<Go1Info />} />
                        <Route path="interface" element={<InterfacePage />} />
                        <Route path="*" element={<h2>Page not found</h2>} />
                    </Route>
                </Routes>
            </BrowserRouter>
        </>
    );
}
