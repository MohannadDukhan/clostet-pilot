// src/pages/SignUp.jsx
import { useState } from "react";
import { Link, useNavigate, useOutletContext } from "react-router-dom";
import Container from "../components/Container";
import { signup } from "../api";

export default function SignUp() {
  const { setUser } = useOutletContext();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [city, setCity] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function validate() {
    if (!email.trim() || !email.includes("@")) return "Enter a valid email address.";
    if (password.length < 8) return "Password must be at least 8 characters.";
    if (!/\d/.test(password)) return "Password must contain at least one number.";
    if (password !== confirmPassword) return "Passwords do not match.";
    if (!city.trim()) return "City is required for weather-based outfit suggestions.";
    return null;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      const { token, user } = await signup({
        email: email.trim().toLowerCase(),
        password,
        city: city.trim(),
      });
      localStorage.setItem("cp:token", token);
      localStorage.setItem("cp:user", JSON.stringify(user));
      if (setUser) setUser(user);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Sign up failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container className="max-w-md">
      <h2 className="text-2xl font-semibold mb-2">create your account</h2>
      <p className="text-text-muted mb-6 text-sm">
        your wardrobe and outfits will be tied to your account — accessible from any device.
      </p>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="block text-sm text-text-muted mb-1">Email</label>
          <input
            type="email"
            className="w-full rounded-xl bg-panel border border-border px-3 py-2 outline-none focus:border-accent/80"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </div>

        <div>
          <label className="block text-sm text-text-muted mb-1">Password</label>
          <input
            type="password"
            className="w-full rounded-xl bg-panel border border-border px-3 py-2 outline-none focus:border-accent/80"
            placeholder="at least 8 chars, must include a number"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
          />
        </div>

        <div>
          <label className="block text-sm text-text-muted mb-1">Confirm password</label>
          <input
            type="password"
            className="w-full rounded-xl bg-panel border border-border px-3 py-2 outline-none focus:border-accent/80"
            placeholder="repeat your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
          />
        </div>

        <div>
          <label className="block text-sm text-text-muted mb-1">City</label>
          <input
            className="w-full rounded-xl bg-panel border border-border px-3 py-2 outline-none focus:border-accent/80"
            placeholder="used for weather-based outfit suggestions"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
          />
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-400">
            {error}
          </div>
        )}

        <button
          className="btn btn-accent breathe w-full"
          disabled={loading}
        >
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-text-muted">
        already have an account?{" "}
        <Link to="/login" className="text-accent hover:underline">
          log in
        </Link>
      </p>
    </Container>
  );
}
