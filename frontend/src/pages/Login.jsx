// src/pages/Login.jsx
import { useState } from "react";
import { Link, useNavigate, useOutletContext } from "react-router-dom";
import Container from "../components/Container";
import { login } from "../api";

export default function Login() {
  const { setUser } = useOutletContext();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const { token, user } = await login({
        email: email.trim().toLowerCase(),
        password,
      });
      localStorage.setItem("cp:token", token);
      localStorage.setItem("cp:user", JSON.stringify(user));
      if (setUser) setUser(user);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Login failed. Check your email and password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container className="max-w-md">
      <h2 className="text-2xl font-semibold mb-2">welcome back</h2>
      <p className="text-text-muted mb-6 text-sm">
        log in to access your wardrobe from any device.
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
            placeholder="your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
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
          {loading ? "Logging in…" : "Log in"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-text-muted">
        don't have an account?{" "}
        <Link to="/signup" className="text-accent hover:underline">
          sign up
        </Link>
      </p>
    </Container>
  );
}
