import { Toaster } from "react-hot-toast";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import RootLayout from "./layouts/RootLayout";

import Home from "./pages/Home";
import About from "./pages/About";
import CreateUser from "./pages/CreateUser";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import NotFound from "./pages/NotFound";
import GenerateOutfit from "./pages/GenerateOutfit";


export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-center" />
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<Home />} />
          <Route path="about" element={<About />} />
          <Route path="create-user" element={<CreateUser />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="upload" element={<Upload />} />
          <Route path="*" element={<NotFound />} />
          <Route path="generate" element={<GenerateOutfit />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
