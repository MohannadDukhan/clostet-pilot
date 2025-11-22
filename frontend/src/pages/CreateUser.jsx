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
  const [showCityWarning, setShowCityWarning] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault(); // stops page from reloading after form submission
    
    // Check if city is missing and show fancy warning
    if (!city.trim()) {
      setShowCityWarning(true);
      setTimeout(() => setShowCityWarning(false), 3000);
      return;
    }
    
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
            placeholder="where do you live?"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
          />
        </div>

        <button
          className="btn btn-accent breathe w-full"
          disabled={!name.trim()}
        >
          Continue
        </button>
      </form>

      {/* Fancy city warning modal */}
      {showCityWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn">
          <div className="bg-gradient-to-br from-orange-500 to-red-500 p-8 rounded-3xl shadow-2xl max-w-md mx-4 animate-bounceIn transform scale-100">
            <div className="text-center">
              <div className="text-6xl mb-4 animate-pulse">🌍</div>
              <h3 className="text-2xl font-bold text-white mb-2">Hold on!</h3>
              <p className="text-white/90 text-lg mb-4">
                We need to know your city to give you weather-appropriate outfit suggestions!
              </p>
              <button
                onClick={() => setShowCityWarning(false)}
                className="bg-white text-orange-600 font-semibold px-6 py-3 rounded-full hover:bg-orange-50 transition-all transform hover:scale-105"
              >
                Got it! 👍
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 rounded bg-red-100 text-red-800 border border-red-200">
          <strong>Error:</strong> {error}
        </div>
      )}
    </Container>
  );
}
