// src/pages/EditProfile.jsx
import { useEffect, useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import Container from "../components/Container";
import { updateUser } from "../api";

export default function EditProfile() {
  const { setUser } = useOutletContext();
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const existing = getUser();
    if (!existing) {
      // no profile yet -> go through the normal flow
      navigate("/create-user", { replace: true });
      return;
    }
    setName(existing.name || "");
    setCity(existing.city || "");
  }, [navigate]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    const existing = getUser();
    if (!existing) {
      navigate("/create-user", { replace: true });
      return;
    }

    const payload = {
      name: name.trim(),
      city: city.trim(),
    };

    if (!payload.name || !payload.city) {
      setError("Both name and city are required.");
      return;
    }

    try {
      const updated = await updateUser(existing.id, payload);
      localStorage.setItem("cp:user", JSON.stringify(updated));
      if (setUser) setUser(updated);
      navigate("/dashboard");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      let msg = err?.message || "Request failed";

      if (Array.isArray(detail)) {
        msg = detail
          .map((d) => {
            const loc = Array.isArray(d.loc) ? d.loc.join(".") : d.loc || "";
            return loc ? `${loc}: ${d.msg}` : d.msg || JSON.stringify(d);
          })
          .join("; ");
      } else if (typeof detail === "string") {
        msg = detail;
      }

      setError(msg);
    }
  }

  return (
    <Container className="max-w-md">
      <h2 className="text-2xl font-semibold mb-2">Edit your profile</h2>
      <p className="text-text-muted mb-6 text-sm">
        Update the name and city attached to your wardrobe. this is also used
        for weather-based outfits.
      </p>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="block text-sm text-text-muted mb-1">Name</label>
          <input
            className="w-full rounded-xl bg-panel border border-border px-3 py-2 outline-none focus:border-accent/80"
            placeholder="your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-sm text-text-muted mb-1">City</label>
          <input
            className="w-full rounded-xl bg-panel border border-border px-3 py-2 outline-none focus:border-accent/80"
            placeholder="your city"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
          />
        </div>

        <button
          className="btn btn-accent breathe w-full"
          disabled={!name.trim() || !city.trim()}
        >
          Save changes
        </button>
      </form>

      {error && (
        <div className="mt-4 p-3 rounded bg-red-100 text-red-800 border border-red-200 text-sm">
          <strong>Error:</strong> {error}
        </div>
      )}
    </Container>
  );
}

function getUser() {
  try {
    const raw = localStorage.getItem("cp:user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
