
import { BrowserRouter, Routes, Route } from "react-router-dom";

import { InterfacePage } from "./pages/interface/interface";
import { MainPage } from "./pages/main";
import { SpotInfo } from "./pages/information/spotInfo";
import { TelloInfo } from "./pages/information/telloInfo";
import { Go1Info } from "./pages/information/unitree";

export default function App() {

  return (
    <>
      <h1>Robot Station Video Manager</h1>
      <button><a href="/interface" >Go to interface</a></button>
      <button><a href="/Spot" >SPOT info</a></button>
      <button><a href="/Tello" >Tello info</a></button>
      <button><a href="/Go1" >Go1 info</a></button>
      <BrowserRouter>
        <Routes>
          <Route path="/" >
            <Route path="main" element={<MainPage />} />
            <Route path="Spot" element={<SpotInfo />} />
            <Route path="Tello" element={<TelloInfo />} />
            <Route path="Go1" element={<Go1Info />} />
            <Route path="interface" element={<InterfacePage />} />

            <Route path="*" element={<h2>Page not found</h2>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </>


  );
}


