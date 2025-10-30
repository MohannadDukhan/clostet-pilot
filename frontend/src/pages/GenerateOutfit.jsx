import { useEffect, useState } from "react";
import Container from "../components/Container";
import { listUserItems } from "../api";
import { useNavigate } from "react-router-dom";

export default function GenerateOutfit() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const user = getUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate("/create-user", { replace: true });
      return;
    }
    let ignore = false;
    (async () => {
      try {
        const data = await listUserItems(user.id);
        if (!ignore) setItems(data || []);
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; };
  }, [user, navigate]);

  if (!user) return null;

  return (
    <Container>
      <div className="max-w-xl mx-auto space-y-6 text-center">
        <h2 className="text-3xl font-semibold">Generate Outfit</h2>
        <p className="text-text-muted">
          This feature will soon let you create AI-powered outfit combinations
          using your uploaded wardrobe items.
        </p>

        {loading ? (
          <div className="text-text-muted mt-6">Loading wardrobe…</div>
        ) : (
          <div className="card p-6 space-y-3">
            <div className="text-sm text-text-muted">
              You currently have <b>{items.length}</b> item
              {items.length !== 1 && "s"} in your wardrobe.
            </div>

            <div className="grid gap-2 text-sm">
              <select className="input w-full">
                <option>Any Season</option>
                <option>Summer</option>
                <option>Fall</option>
                <option>Winter</option>
                <option>Spring</option>
              </select>
              <select className="input w-full">
                <option>Any Formality</option>
                <option>Casual</option>
                <option>Business Casual</option>
                <option>Formal</option>
                <option>Streetwear</option>
              </select>
            </div>

            <button
              className="btn btn-accent breathe w-full opacity-60 cursor-not-allowed"
              disabled
            >
              Generate (coming soon)
            </button>

            <a
              href="/dashboard"
              className="text-xs text-accent hover:underline block mt-2"
            >
              ← Back to wardrobe
            </a>
          </div>
        )}
      </div>
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
