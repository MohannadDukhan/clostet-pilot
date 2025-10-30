import { Link, NavLink } from "react-router-dom";
import { Sparkles, Upload, UserPlus, Shirt, Info } from "lucide-react";

const navLinkClass = ({ isActive }) =>
  `px-3 py-2 rounded-xl transition-all hover:opacity-90 ${isActive ? "bg-panel/60 border border-border" : "hover:bg-panel/40"}`;

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 bg-bg/70 backdrop-blur border-b border-border">
      <nav className="max-w-6xl mx-auto flex items-center justify-between px-4 h-16">
        <Link to="/" className="flex items-center gap-2">
          <div className="size-8 rounded-xl bg-gradient-to-br from-accent/90 to-accent/60 shadow-[var(--shadow-soft)] grid place-items-center">
            <Sparkles className="size-4 text-bg" />
          </div>
          <span className="font-semibold tracking-tight">Closet Pilot</span>
        </Link>

        <div className="hidden sm:flex items-center gap-1 text-sm">
          <NavLink to="/" className={navLinkClass}>Home</NavLink>
          <NavLink to="/about" className={navLinkClass}><Info className="inline-block mr-1 size-4" />About</NavLink>
          <NavLink to="/create-user" className={navLinkClass}><UserPlus className="inline-block mr-1 size-4" />Create User</NavLink>
          <NavLink to="/dashboard" className={navLinkClass}><Shirt className="inline-block mr-1 size-4" />Wardrobe</NavLink>
          <NavLink to="/upload" className={navLinkClass}><Upload className="inline-block mr-1 size-4" />Upload</NavLink>
          <NavLink to="/generate" className={navLinkClass}> Generate </NavLink>
        </div>

        <Link to="/create-user" className="btn btn-accent breathe hidden sm:inline-flex">
          Get Started
        </Link>
      </nav>
    </header>
  );
}