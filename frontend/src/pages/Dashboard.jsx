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
                      <label className="text-xs font-medium mb-1">Outfit Part</label>
                      <select
                        className="input w-full"
                        value={e.outfit_part || it.outfit_part || ""}
                        onChange={ev => onChange(it.id, "outfit_part", ev.target.value)}
                      >
                        <option value="">Select outfit part</option>
                        <option value="top">Top</option>
                        <option value="bottom">Bottom</option>
                        <option value="dress">Dress</option>
                        <option value="outerwear">Outerwear</option>
                        <option value="shoes">Shoes</option>
                        <option value="accessory">Accessory</option>
                      </select>
                      <label className="text-xs font-medium mb-1">Category</label>
                      <select
                        className="input w-full"
                        value={e.category || it.category || ""}
                        onChange={ev => onChange(it.id, "category", ev.target.value)}
                      >
                        <option value="">Select category</option>
                        <option value="t_shirt">T-Shirt</option>
                        <option value="shirt">Shirt</option>
                        <option value="polo">Polo</option>
                        <option value="sweater">Sweater</option>
                        <option value="tank_top">Tank Top</option>
                        <option value="hoodie">Hoodie</option>
                        <option value="dress">Dress</option>
                        <option value="crop_top">Crop Top</option>
                        <option value="leggings">Leggings</option>
                        <option value="shorts">Shorts</option>
                        <option value="skirt">Skirt</option>
                        <option value="pants">Pants</option>
                        <option value="jeans">Jeans</option>
                        <option value="chinos">Chinos</option>
                        <option value="jacket">Jacket</option>
                        <option value="coat">Coat</option>
                        <option value="blazer">Blazer</option>
                        <option value="cardigan">Cardigan</option>
                        <option value="leather_jacket">Leather Jacket</option>
                        <option value="puffer_jacket">Puffer Jacket</option>
                        <option value="sneakers">Sneakers</option>
                        <option value="boots">Boots</option>
                        <option value="sandals">Sandals</option>
                        <option value="dress_shoes">Dress Shoes</option>
                        <option value="heels">Heels</option>
                        <option value="flats">Flats</option>
                        <option value="loafers">Loafers</option>
                        <option value="hat">Hat</option>
                        <option value="scarf">Scarf</option>
                        <option value="belt">Belt</option>
                        <option value="bag">Bag</option>
                        <option value="jewelry">Jewelry</option>
                        <option value="watch">Watch</option>
                      </select>
                      <Input
                        label="Primary color"
                        value={e.primary_color}
                        onChange={(v) => onChange(it.id, "primary_color", v)}
                      />
                      <label className="text-xs font-medium mb-1">Formality</label>
                      <select
                        className="input w-full"
                        value={e.formality || it.formality || ""}
                        onChange={ev => onChange(it.id, "formality", ev.target.value)}
                      >
                        <option value="">Select formality</option>
                        <option value="casual">Casual</option>
                        <option value="smart_casual">Smart Casual</option>
                        <option value="semi_formal">Semi Formal</option>
                        <option value="formal">Formal</option>
                        <option value="business_casual">Business Casual</option>
                        <option value="sporty">Sporty</option>
                      </select>
                      <label className="text-xs font-medium mb-1">Season</label>
                      <select
                        className="input w-full"
                        value={e.season || it.season || ""}
                        onChange={ev => onChange(it.id, "season", ev.target.value)}
                      >
                        <option value="">Select season</option>
                        <option value="summer">Summer</option>
                        <option value="winter">Winter</option>
                        <option value="all_season">All Season</option>
                        <option value="spring">Spring</option>
                        <option value="fall">Fall</option>
                      </select>
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
