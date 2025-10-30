import Container from "../components/Container";
import { useEffect, useState, useMemo } from "react";
import {
  listUserItems,
  deleteItem,
  patchItem,
  classifyItem,
  imageSrc,
} from "../api";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editMap, setEditMap] = useState({});
  const [expanded, setExpanded] = useState({});
  const [busyId, setBusyId] = useState(null);
  const navigate = useNavigate();

  const user = useMemo(() => getUser(), []);

  useEffect(() => {
  if (!user) {
    navigate("/create-user", { replace: true });
    return;
  }
  let ignore = false;
  (async () => {
    try {
      const data = await listUserItems(user.id);
      if (!ignore) {
        setItems(data || []);
        const e = {};
        const exp = {};
        for (const it of data || []) {
          e[it.id] = {
            category: it.category || "",
            primary_color: it.primary_color || it.color || "",
            season: it.season || "",
            formality: it.formality || "",
            notes: it.notes || "",
            verified: !!it.verified,
          };
          exp[it.id] = false;
        }
        setEditMap(e);
        setExpanded(exp);
      }
    } finally {
      if (!ignore) setLoading(false);
    }
  })();
  return () => { ignore = true; };
}, [user?.id, navigate]);   // <<— was [user, navigate]


  if (!user) return null;

  function onChange(id, key, value) {
    setEditMap((m) => ({
      ...m,
      [id]: { ...m[id], [key]: value },
    }));
  }

  function toggleExpand(id, state) {
    setExpanded((m) => ({ ...m, [id]: state }));
  }

  return (
    <Container>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold">Your Wardrobe</h2>
        <a href="/upload" className="btn btn-accent breathe">
          Upload
        </a>
      </div>

      {loading ? (
        <div className="text-text-muted">Loading…</div>
      ) : items.length === 0 ? (
        <div className="card p-6 text-text-muted">
          No items yet. Try uploading something.
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
          {items.map((it) => {
            const e = editMap[it.id] || {};
            const isOpen = expanded[it.id];
            const colorChip =
              e.primary_color || it.primary_color || it.color || "";

            return (
              <div key={it.id} className="card p-3 space-y-2">
                <div className="aspect-square rounded-xl bg-panel/40 border border-border overflow-hidden grid place-items-center">
                  {imageSrc(it) ? (
                    <img
                      src={imageSrc(it)}
                      alt={it.name || it.original_filename || "Item"}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-xs text-text-muted">No image</div>
                  )}
                </div>

                <div className="text-sm font-medium">
                  {it.name || it.original_filename || "Unnamed item"}
                </div>

                {!isOpen ? (
                  <>
                    <div className="text-xs text-text-muted">
                      {[
                        e.category || it.category,
                        colorChip,
                        e.season || it.season,
                        e.formality || it.formality,
                      ]
                        .filter(Boolean)
                        .join(" • ")}
                    </div>
                    <div className="flex gap-2 mt-2">
                      <button
                        className="btn"
                        onClick={() => toggleExpand(it.id, true)}
                      >
                        Edit
                      </button>
                      <button
                        className="btn"
                        onClick={async () => {
                          setBusyId(it.id);
                          try {
                            const updated = await classifyItem(it.id);
                            setItems((prev) =>
                              prev.map((x) =>
                                x.id === it.id ? updated : x
                              )
                            );
                            setEditMap((m) => ({
                              ...m,
                              [it.id]: {
                                category: updated.category || "",
                                primary_color:
                                  updated.primary_color ||
                                  updated.color ||
                                  "",
                                season: updated.season || "",
                                formality: updated.formality || "",
                                notes: updated.notes || "",
                                verified: !!updated.verified,
                              },
                            }));
                          } finally {
                            setBusyId(null);
                          }
                        }}
                        disabled={busyId === it.id}
                      >
                        {busyId === it.id ? "Classifying…" : "Re-classify"}
                      </button>
                      <button
                        className="btn"
                        onClick={async () => {
                          await deleteItem(it.id);
                          setItems((p) => p.filter((x) => x.id !== it.id));
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="grid gap-2 text-sm">
                      <Input
                        label="Category"
                        value={e.category}
                        onChange={(v) => onChange(it.id, "category", v)}
                      />
                      <Input
                        label="Primary color"
                        value={e.primary_color}
                        onChange={(v) => onChange(it.id, "primary_color", v)}
                      />
                      <Input
                        label="Season"
                        value={e.season}
                        onChange={(v) => onChange(it.id, "season", v)}
                      />
                      <Input
                        label="Formality"
                        value={e.formality}
                        onChange={(v) => onChange(it.id, "formality", v)}
                      />
                      <TextArea
                        label="Notes"
                        value={e.notes}
                        onChange={(v) => onChange(it.id, "notes", v)}
                      />
                      <label className="text-xs flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={!!e.verified}
                          onChange={(ev) =>
                            onChange(it.id, "verified", ev.target.checked)
                          }
                        />
                        Verified
                      </label>
                    </div>

                    <div className="flex gap-2 mt-2">
                      <button
                        className="btn btn-accent"
                        onClick={async () => {
                          setBusyId(it.id);
                          try {
                            const updated = await patchItem(it.id, editMap[it.id]);
                            setItems((p) =>
                              p.map((x) => (x.id === it.id ? updated : x))
                            );
                            toggleExpand(it.id, false);
                          } finally {
                            setBusyId(null);
                          }
                        }}
                      >
                        {busyId === it.id ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn"
                        onClick={() => toggleExpand(it.id, false)}
                      >
                        Cancel
                      </button>
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Container>
  );
}

function Input({ label, value, onChange }) {
  return (
    <label className="text-xs grid gap-1">
      <span className="text-text-muted">{label}</span>
      <input
        className="input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={label}
      />
    </label>
  );
}

function TextArea({ label, value, onChange }) {
  return (
    <label className="text-xs grid gap-1">
      <span className="text-text-muted">{label}</span>
      <textarea
        className="input"
        rows={3}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={label}
      />
    </label>
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
