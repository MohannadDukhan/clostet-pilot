// src/pages/CreateUser.jsx
import { useState } from "react";
import Container from "../components/Container";
import { createUser } from "../api";
import { useNavigate } from "react-router-dom";

export default function CreateUser() {
  const [name, setName] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    const user = await createUser(name.trim());
    // persist for dashboard/upload
    localStorage.setItem("cp:user", JSON.stringify(user));
    navigate("/dashboard", { replace: true });
  }

  return (
    <Container className="max-w-md">
      <h2 className="text-2xl font-semibold mb-4">Create a local user</h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          className="input w-full"
          placeholder="Your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <button className="btn btn-accent breathe w-full" disabled={!name.trim()}>
          Continue
        </button>
      </form>
    </Container>
  );
}
