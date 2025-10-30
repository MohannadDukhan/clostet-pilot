import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Navbar from "../components/Navbar";
import { useState, useEffect } from "react";

export default function RootLayout() {
  const location = useLocation();
  const [user, setUser] = useState(null);
  useEffect(() => {
    try {
      const raw = localStorage.getItem("cp:user");
      if (raw) {
        setUser(JSON.parse(raw));
      }
    } catch {
      setUser(null);
    }
  }, []);

  return (
    <div className="min-h-dvh bg-gradient-to-b from-bg to-surface text-text">
      <Navbar user={user} setUser={setUser} />
      <AnimatePresence mode="wait">
        <motion.main
          key={location.pathname}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.25 }}
          className="py-10"
        >
          <Outlet context={{ setUser }} />
        </motion.main>
      </AnimatePresence>
      <footer className="py-10 border-t border-border/60">
        <div className="max-w-6xl mx-auto px-4 text-xs text-text-muted">
          Built by Carleton University Software Engineering Capstone Team
        </div>
      </footer>
    </div>
  );
}