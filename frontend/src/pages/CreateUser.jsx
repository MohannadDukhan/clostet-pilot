// src/pages/CreateUser.jsx
import { useState } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import Container from "../components/Container";
import { createUser } from "../api";

export default function CreateUser() {
  const { setUser } = useOutletContext();
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault(); // stops page from reloading after form submission
    const payload = {
      name: name.trim(),
      city: city.trim(),
    };

    try {
      const user = await createUser(payload); // send to backend
      // persist server response (includes id)
      localStorage.setItem("cp:user", JSON.stringify(user));
      if (setUser) setUser(user); // update navbar instantly
      navigate("/dashboard", { replace: true }); // redirect to dashboard
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
      } else if (detail) {
        try {
          msg = JSON.stringify(detail);
        } catch {
          msg = String(detail);
        }
      }
      setError(String(msg));
    }
  }

  return (
    <Container className="max-w-md">
      <h2 className="text-2xl font-semibold mb-2">create your profile</h2>
      <p className="text-text-muted mb-6">
        this will keep your wardrobe and outfits separate from other users.
      </p>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="block text-sm text-text-muted mb-1">Name</label>
          <input
            className="w-full rounded-xl bg-panel border border-border px-3 py-2 outline-none focus:border-accent/80"
            placeholder="what should we call you?"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-sm text-text-muted mb-1">City</label>
          <input
            className="w-full rounded-xl bg-panel border border-border px-3 py-2 outline-none focus:border-accent/80"
            placeholder="optional"
            value={city}
            onChange={(e) => setCity(e.target.value)}
          />
        </div>

        <button
          className="btn btn-accent breathe w-full"
          disabled={!name.trim()}
        >
          Continue
        </button>
      </form>

      {error && (
        <div className="mt-4 p-3 rounded bg-red-100 text-red-800 border border-red-200">
          <strong>Error:</strong> {error}
        </div>
      )}
    </Container>
  );
}
