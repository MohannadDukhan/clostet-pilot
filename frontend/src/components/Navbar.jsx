import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { Sparkles, Upload, Shirt, LogIn, UserPlus, Menu, X } from "lucide-react";

export default function Navbar({ user, setUser }) {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const navLinkClass = ({ isActive }) =>
    `px-3 py-2 rounded-xl transition-all hover:opacity-90 ${
      isActive ? "bg-panel/60 border border-border" : "hover:bg-panel/40"
    }`;

  const mobileNavLinkClass = ({ isActive }) =>
    `block px-4 py-3 rounded-xl transition-all text-sm ${
      isActive ? "bg-panel/60 border border-border" : "hover:bg-panel/40"
    }`;

  function handleLogout(e) {
    e.preventDefault();
    localStorage.removeItem("cp:token");
    localStorage.removeItem("cp:user");
    setUser(null);
    navigate("/login");
    setMenuOpen(false);
  }

  return (
    <header className="border-b border-border/60 relative">
      <nav className="max-w-6xl mx-auto px-4 flex items-center justify-between h-16 gap-4">
        {/* left: logo + nav */}
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-accent text-primary shadow-sm">
              <Sparkles size={18} />
            </span>
            <span className="font-semibold text-sm tracking-wide">
              Outfit Maker
            </span>
          </Link>

          {user && (
            <div className="hidden md:flex items-center gap-1 text-xs">
              <NavLink to="/" className={navLinkClass} end>
                Home
              </NavLink>
              <NavLink to="/dashboard" className={navLinkClass}>
                <span className="inline-flex items-center gap-1">
                  <Shirt size={12} /> Wardrobe
                </span>
              </NavLink>
              <NavLink to="/upload" className={navLinkClass}>
                <span className="inline-flex items-center gap-1">
                  <Upload size={12} /> Upload
                </span>
              </NavLink>
              <NavLink to="/generate" className={navLinkClass}>
                Generate
              </NavLink>
              <NavLink to="/style-lab" className={navLinkClass}>
                <span className="inline-flex items-center gap-1">
                  🧪 Style Lab
                </span>
              </NavLink>
            </div>
          )}

          {!user && (
            <div className="hidden md:flex items-center gap-1 text-xs">
              <NavLink to="/" className={navLinkClass} end>
                Home
              </NavLink>
            </div>
          )}
        </div>

        {/* right: user controls + mobile menu button */}
        <div className="flex items-center gap-3 text-xs">
          {user ? (
            <>
              <Link
                to="/profile"
                className="hidden sm:inline-flex items-center rounded-xl bg-panel/70 border border-border px-3 py-1.5 text-xs"
              >
                {user.name || user.email || "Profile"}
              </Link>

              <button
                type="button"
                className="text-[11px] text-text-muted hover:underline underline-offset-2 hidden md:inline"
                onClick={handleLogout}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className="inline-flex items-center gap-1 text-[11px] hover:underline underline-offset-2 hidden md:inline-flex"
              >
                <LogIn size={12} /> Log in
              </NavLink>

              <Link to="/signup" className="btn btn-accent breathe text-xs inline-flex items-center gap-1 hidden md:inline-flex">
                <UserPlus size={12} /> Sign up
              </Link>
            </>
          )}

          {/* mobile menu toggle */}
          <button
            type="button"
            className="md:hidden p-2 rounded-xl hover:bg-panel/40 transition-all"
            onClick={() => setMenuOpen((o) => !o)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </nav>

      {/* mobile dropdown */}
      {menuOpen && (
        <div className="md:hidden absolute top-16 left-0 right-0 z-50 border-b border-border/60 bg-[var(--color-bg,#fff)] shadow-lg px-4 py-3 flex flex-col gap-1">
          {user ? (
            <>
              <NavLink to="/" className={mobileNavLinkClass} end onClick={() => setMenuOpen(false)}>
                Home
              </NavLink>
              <NavLink to="/dashboard" className={mobileNavLinkClass} onClick={() => setMenuOpen(false)}>
                <span className="inline-flex items-center gap-2">
                  <Shirt size={14} /> Wardrobe
                </span>
              </NavLink>
              <NavLink to="/upload" className={mobileNavLinkClass} onClick={() => setMenuOpen(false)}>
                <span className="inline-flex items-center gap-2">
                  <Upload size={14} /> Upload
                </span>
              </NavLink>
              <NavLink to="/generate" className={mobileNavLinkClass} onClick={() => setMenuOpen(false)}>
                Generate
              </NavLink>
              <NavLink to="/style-lab" className={mobileNavLinkClass} onClick={() => setMenuOpen(false)}>
                <span className="inline-flex items-center gap-2">
                  🧪 Style Lab
                </span>
              </NavLink>
              <NavLink to="/profile" className={mobileNavLinkClass} onClick={() => setMenuOpen(false)}>
                {user.name || user.email || "Profile"}
              </NavLink>
              <button
                type="button"
                className="text-left px-4 py-3 rounded-xl text-sm text-text-muted hover:bg-panel/40 transition-all"
                onClick={handleLogout}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/" className={mobileNavLinkClass} end onClick={() => setMenuOpen(false)}>
                Home
              </NavLink>
              <NavLink to="/login" className={mobileNavLinkClass} onClick={() => setMenuOpen(false)}>
                <span className="inline-flex items-center gap-2">
                  <LogIn size={14} /> Log in
                </span>
              </NavLink>
              <NavLink to="/signup" className={mobileNavLinkClass} onClick={() => setMenuOpen(false)}>
                <span className="inline-flex items-center gap-2">
                  <UserPlus size={14} /> Sign up
                </span>
              </NavLink>
            </>
          )}
        </div>
      )}
    </header>
  );
}
