import React, { useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { Sparkles, Upload, UserPlus, Shirt, Info } from "lucide-react";
import { listUsers } from "../api";
export default function Navbar({ user, setUser }) {
  const navLinkClass = ({ isActive }) =>
    `px-3 py-2 rounded-xl transition-all hover:opacity-90 ${isActive ? "bg-panel/60 border border-border" : "hover:bg-panel/40"}`;

  const [showSelect, setShowSelect] = useState(false);
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const navigate = useNavigate();

  function handleLogout(e) {
    e.preventDefault();
    localStorage.removeItem("cp:user");
    setUser(null);
    navigate("/");
  }
  async function handleSwitchUser(e) {
    e.preventDefault();
    setLoadingUsers(true);
    try {
      const allUsers = await listUsers();
      setUsers(allUsers);
      setShowSelect(true);
    } finally {
      setLoadingUsers(false);
    }
  }

  function handleSelectUser(u) {
    localStorage.setItem("cp:user", JSON.stringify(u));
    setUser(u);
    setShowSelect(false);
    window.location.href = "/dashboard";
  }

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

        {/* Right side: either user badge or Get Started button */}
        {user && user.name ? (
          <div className="hidden sm:flex items-center gap-3">
            <div className="px-3 py-1 rounded-lg bg-panel/40 border border-border text-sm flex items-center gap-3">
              <span className="font-medium">{user.name}</span>
              <button onClick={handleSwitchUser} className="text-xs text-blue-600 underline">Switch User</button>
              <button onClick={handleLogout} className="text-xs text-muted underline">Log out</button>
            </div>
          </div>
        ) : (
          <Link to="/create-user" className="btn btn-accent breathe hidden sm:inline-flex">
            Get Started
          </Link>
        )}

        {/* User selection modal */}
        {showSelect && (
          <div className="fixed inset-0 bg-black/30 z-50 flex justify-center" style={{ alignItems: 'flex-start' }}>
            <div className="bg-white rounded-lg shadow-lg p-6 min-w-[320px] max-w-[90vw] mt-[20vh]">
              <h3 className="text-lg font-semibold mb-2">Select user to work on</h3>
              {loadingUsers ? (
                <div>Loading users...</div>
              ) : (
                <ul className="space-y-2 mb-4">
                  {users.map((u) => (
                    <li key={u.id} className="flex items-center justify-between gap-2">
                      <span className="font-medium">{u.name}</span>
                      <button
                        className="btn btn-sm btn-accent"
                        onClick={() => handleSelectUser(u)}
                      >Select</button>
                    </li>
                  ))}
                </ul>
              )}
              <button className="btn btn-muted w-full" onClick={() => setShowSelect(false)}>
                Cancel
              </button>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}

