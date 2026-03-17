import React, { useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { Sparkles, Upload, UserPlus, Shirt } from "lucide-react";
import { listUsers } from "../api";

export default function Navbar({ user, setUser }) {
  const [showSelect, setShowSelect] = useState(false);
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const navigate = useNavigate();

  const navLinkClass = ({ isActive }) =>
    `px-3 py-2 rounded-xl transition-all hover:opacity-90 ${
      isActive ? "bg-panel/60 border border-border" : "hover:bg-panel/40"
    }`;

  function handleLogout(e) {
    e.preventDefault();
    localStorage.removeItem("cp:user");
    setUser(null);
    navigate("/");
  }

    function handleEditProfile(e) {
    e.preventDefault();
    navigate("/profile");
  }

  async function openUserSelect() {
    setShowSelect(true);
    setLoadingUsers(true);
    try {
      const allUsers = await listUsers();
      setUsers(allUsers || []);
    } catch (e) {
      console.error("Failed to load users", e);
    } finally {
      setLoadingUsers(false);
    }
  }

  function handleSelectUser(u) {
    if (!u) return;
    localStorage.setItem("cp:user", JSON.stringify(u));
    setUser(u);
    setShowSelect(false);
    navigate("/dashboard");
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

          <div className="hidden md:flex items-center gap-1 text-xs">
            <NavLink to="/" className={navLinkClass} end>
              Home
            </NavLink>
<NavLink to="/create-user" className={navLinkClass}>
              <span className="inline-flex items-center gap-1">
                <UserPlus size={12} /> Create User
              </span>
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
        </div>

        {/* right: user controls */}
        <div className="flex items-center gap-3 text-xs">
          {user ? (
            <>
              {/* edit current user */}
              <Link
                to="/profile"
                className="hidden sm:inline-flex items-center rounded-xl bg-panel/70 border border-border px-3 py-1.5 text-xs"
              >
                {user.name || "Profile"}
              </Link>

              <button
                type="button"
                className="text-[11px] underline-offset-2 hover:underline"
                onClick={openUserSelect}
              >
                Switch user
              </button>

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
              {/* this is the important fix: switch user is still available when logged out */}
              <button
                type="button"
                className="text-[11px] underline-offset-2 hover:underline"
                onClick={openUserSelect}
              >
                Switch user
              </button>

              <Link
                to="/create-user"
                className="btn btn-accent breathe text-xs"
              >
                Get started
              </Link>
            </>
          )}
        </div>

        {/* user select overlay */}
        {showSelect && (
          <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60">
            <div className="card bg-panel max-w-sm w-full mx-4 p-5 space-y-3">
              <h2 className="text-sm font-semibold">Select a wardrobe</h2>
              <p className="text-[11px] text-text-muted">
                Pick an existing user to continue with their wardrobe. You can
                always create a new one later.
              </p>

              {loadingUsers ? (
                <div className="text-xs text-text-muted">Loading users…</div>
              ) : users.length === 0 ? (
                <div className="text-xs text-text-muted">
                  No saved users yet. Create your first profile to get started.
                </div>
              ) : (
                <ul className="space-y-1 max-h-52 overflow-y-auto text-sm">
                  {users.map((u) => (
                    <li key={u.id}>
                      <button
                        type="button"
                        onClick={() => handleSelectUser(u)}
                        className="w-full text-left px-3 py-2 rounded-xl hover:bg-panel/70 border border-transparent hover:border-border transition"
                      >
                        <div className="font-medium text-xs">{u.name}</div>
                        <div className="text-[11px] text-text-muted">
                          {u.city || "No city set"}
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  className="btn btn-muted text-xs"
                  onClick={() => setShowSelect(false)}
                >
                  Close
                </button>
                {!user && (
                  <Link
                    to="/create-user"
                    className="btn btn-accent text-xs"
                    onClick={() => setShowSelect(false)}
                  >
                    New profile
                  </Link>
                )}
              </div>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
