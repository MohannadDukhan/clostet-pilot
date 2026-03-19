import { Link, NavLink, useNavigate } from "react-router-dom";
import { Sparkles, Upload, Shirt, LogIn, UserPlus } from "lucide-react";

export default function Navbar({ user, setUser }) {
  const navigate = useNavigate();

  const navLinkClass = ({ isActive }) =>
    `px-3 py-2 rounded-xl transition-all hover:opacity-90 ${
      isActive ? "bg-panel/60 border border-border" : "hover:bg-panel/40"
    }`;

  function handleLogout(e) {
    e.preventDefault();
    localStorage.removeItem("cp:token");
    localStorage.removeItem("cp:user");
    setUser(null);
    navigate("/login");
  }

  return (
    <header className="border-b border-border/60">
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

        {/* right: user controls */}
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
                className="text-[11px] text-text-muted hover:underline underline-offset-2"
                onClick={handleLogout}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className="inline-flex items-center gap-1 text-[11px] hover:underline underline-offset-2"
              >
                <LogIn size={12} /> Log in
              </NavLink>

              <Link to="/signup" className="btn btn-accent breathe text-xs inline-flex items-center gap-1">
                <UserPlus size={12} /> Sign up
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
