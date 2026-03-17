import { Toaster } from "react-hot-toast";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import RootLayout from "./layouts/RootLayout";

import Home from "./pages/Home";
import CreateUser from "./pages/CreateUser";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import NotFound from "./pages/NotFound";
import GenerateOutfit from "./pages/GenerateOutfit";
import EditProfile from "./pages/EditProfile";
import StyleLab from "./pages/StyleLab";


export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-center" />
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<Home />} />
<Route path="create-user" element={<CreateUser />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="upload" element={<Upload />} />
          <Route path="profile" element={<EditProfile />} />   {/* new */}
          <Route path="generate" element={<GenerateOutfit />} />
          <Route path="style-lab" element={<StyleLab />} />
          <Route path="*" element={<NotFound />} />
        </Route>

      </Routes>
    </BrowserRouter>
  );
}
