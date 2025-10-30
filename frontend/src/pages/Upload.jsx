// src/pages/Upload.jsx
import { useState } from "react";
import Container from "../components/Container";
import { uploadUserItem } from "../api";
import { useNavigate } from "react-router-dom";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const navigate = useNavigate();

  const user = getUser();
  if (!user) {
    navigate("/create-user", { replace: true });
    return null;
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    await uploadUserItem(user.id, { file, name });
    setFile(null);
    setName("");
    navigate("/dashboard");
  }

  return (
    <Container className="max-w-lg">
      <h2 className="text-2xl font-semibold mb-4">Upload</h2>
      <form onSubmit={handleUpload} className="space-y-3">
        <input
          className="input w-full"
          placeholder="Optional name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <div className="card p-6">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm"
          />
          <p className="text-xs text-text-muted mt-2">
            AI classification runs automatically if enabled on the server.
          </p>
        </div>
        <button className="btn btn-accent breathe w-full" disabled={!file}>Upload</button>
      </form>
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
