// src/pages/CreateUser.jsx
import { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import Container from "../components/Container";
import { createUser } from "../api";
import { useNavigate } from "react-router-dom";

export default function CreateUser() {
  const { setUser } = useOutletContext();
  const [name, setName] = useState("");
  const [gender, setGender] = useState("");
  const [city, setCity] = useState("");
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault(); //stops page from reloading after form submission
    const payload = { name: name.trim(), gender: gender.trim(), city: city.trim() }; //create obj
    try {
      const user = await createUser(payload); //send to backend
      // persist server response (includes id)
  localStorage.setItem("cp:user", JSON.stringify(user)); //save info in browser storage
  if (setUser) setUser(user); // update navbar instantly
  navigate("/dashboard", { replace: true }); //redirect to dashboard
    } catch (err) {
      const detail = err?.response?.data?.detail; //read error
      let msg = err?.message || "Request failed"; //if nothing put this
      if (Array.isArray(detail)) {
        msg = detail.map((d) => { //if multiple errors
          const loc = Array.isArray(d.loc) ? d.loc.join(".") : d.loc || "";
          return loc ? `${loc}: ${d.msg}` : d.msg || JSON.stringify(d);
        }).join("; ");
      } else if (detail) {
        try { msg = JSON.stringify(detail); } catch { msg = String(detail); }
      }
      setError(String(msg));
    }
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
        <select
          value={gender}
          onChange={(e) => setGender(e.target.value)}
          className="input w-full"
          required
        >
          <option value="">Select your gender</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
        </select>
        <input
          className="input w-full"
          placeholder="Your city"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          required
        />
        <button className="btn btn-accent breathe w-full" disabled={!name.trim()}>
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
