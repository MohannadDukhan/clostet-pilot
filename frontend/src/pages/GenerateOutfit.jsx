import { useEffect, useState } from "react";
import { API, listUsers, listUserItems, suggestOutfit } from "../api";

// helper to resolve image URLs whether absolute or served from /storage
function imageSrc(item) {
  const url = item?.image_url || "";
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  const base = (API?.defaults?.baseURL || "").replace(/\/$/, "");
  const path = url.startsWith("/storage") ? url : `/storage/${url}`;
  return `${base}${path}`;
}

const SEASONS = [
  { value: "any", label: "any" },
  { value: "all_season", label: "all season" },
  { value: "spring", label: "spring" },
  { value: "spring_summer", label: "spring / summer" },
  { value: "summer", label: "summer" },
  { value: "fall", label: "fall" },
  { value: "fall_winter", label: "fall / winter" },
  { value: "winter", label: "winter" },
];


const FORMALITY = [
  { value: "any", label: "any" },
  { value: "casual", label: "casual" },
  { value: "smart_casual", label: "smart casual" },
  { value: "semi_formal", label: "semi formal" },
  { value: "formal", label: "formal" },
];


export default function GenerateOutfit() {
  // user state (self-managed)
  const [users, setUsers] = useState([]);
  const [userId, setUserId] = useState(null);

  const [items, setItems] = useState([]);
  const [anchorIds, setAnchorIds] = useState([]);
  const [excludeIds, setExcludeIds] = useState([]);

  const [season, setSeason] = useState("any");
  const [formality, setFormality] = useState("any");
  const [suggestion, setSuggestion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");


  // load users on mount and restore last selection if available
  useEffect(() => {
    (async () => {
      try {
        const list = await listUsers();
        setUsers(list || []);
        const saved = localStorage.getItem("cp:selectedUserId");
        if (saved && list.some(u => String(u.id) === String(saved))) {
          setUserId(Number(saved));
        } else if (list.length) {
          setUserId(list[0].id);
        }
      } catch (e) {
        setErr("failed to load users");
      }
    })();
  }, []);

  // persist selection
  useEffect(() => {
    if (userId != null) localStorage.setItem("cp:selectedUserId", String(userId));
  }, [userId]);

  // load wardrobe items whenever the user changes
  useEffect(() => {
    if (!userId) {
      setItems([]);
      setAnchorIds([]);
      setExcludeIds([]);
      return;
    }

    (async () => {
      try {
        const data = await listUserItems(userId);
        setItems(data || []);
        // reset selections on user change
        setAnchorIds([]);
        setExcludeIds([]);
      } catch (e) {
        console.error("failed to load items", e);
      }
    })();
  }, [userId]);

  function toggleAnchor(id) {
    setAnchorIds((prev) => {
      const exists = prev.includes(id);
      const next = exists ? prev.filter((x) => x !== id) : [...prev, id];
      return next;
    });
    // if we include it, make sure it's not excluded
    setExcludeIds((prev) => prev.filter((x) => x !== id));
  }

  function toggleExclude(id) {
    setExcludeIds((prev) => {
      const exists = prev.includes(id);
      const next = exists ? prev.filter((x) => x !== id) : [...prev, id];
      return next;
    });
    // excluded items can't also be anchors
    setAnchorIds((prev) => prev.filter((x) => x !== id));
  }



  async function handleGenerate(e) {
    e.preventDefault();
    if (!userId) {
      setErr("select a user first");
      return;
    }
    setLoading(true);
    setErr("");
    try {
      const params = { season, formality };

      if (anchorIds.length) {
        params.anchor_ids = anchorIds.join(",");
      }
      if (excludeIds.length) {
        params.exclude_ids = excludeIds.join(",");
      }

      const data = await suggestOutfit(userId, params);

      setSuggestion(data);
    } catch {
      setErr("failed to generate outfit");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-8">
      <h1 className="text-2xl font-semibold">Outfit Generator</h1>
      <p className="text-text-muted mt-1">rule-based v1 while we build model-b</p>

      {/* user + filters */}
      <form className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4" onSubmit={handleGenerate}>
        <div className="card p-4">
          <label className="text-sm text-text-muted">User</label>
          <select
            className="mt-2 w-full bg-panel border border-border rounded-xl p-2"
            value={userId ?? ""}
            onChange={(e) => setUserId(e.target.value ? Number(e.target.value) : null)}
          >
            {!users.length && <option value="">No users</option>}
            {users.map(u => (
              <option key={u.id} value={u.id}>{u.name} • {u.city}</option>
            ))}
          </select>
        </div>

        <div className="card p-4">
          <label className="text-sm text-text-muted">Season</label>
          <select
            className="mt-2 w-full bg-panel border border-border rounded-xl p-2"
            value={season}
            onChange={(e) => setSeason(e.target.value)}
          >
            {SEASONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>

        <div className="card p-4">
          <label className="text-sm text-text-muted">Formality</label>
          <select
            className="mt-2 w-full bg-panel border border-border rounded-xl p-2"
            value={formality}
            onChange={(e) => setFormality(e.target.value)}
          >
            {FORMALITY.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
          </select>
        </div>

        <div className="card p-4 flex items-end">
          <button
            className="w-full rounded-2xl px-4 py-2 bg-green-400/80 hover:bg-green-400 transition breathe"
            type="submit"
            disabled={loading || !userId}
          >
            {loading ? "Generating..." : "Generate"}
          </button>
        </div>
      </form>

      {/* include / exclude items for this suggestion */}
      {userId && items.length > 0 && (
        <div className="mt-6 card p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-sm font-medium">include / exclude items</h2>
              <p className="text-xs text-text-muted mt-1">
                choose pieces you definitely want to wear (include) or hide for this suggestion (exclude).
              </p>
            </div>
            <button
              type="button"
              className="text-xs text-text-muted underline"
              onClick={() => {
                setAnchorIds([]);
                setExcludeIds([]);
              }}
            >
              clear
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-h-80 overflow-y-auto pr-1">
            {items.map((item) => {
              const isAnchor = anchorIds.includes(item.id);
              const isExcluded = excludeIds.includes(item.id);

              return (
                <div
                  key={item.id}
                  className={`rounded-2xl border p-2 text-xs ${
                    isExcluded
                      ? "border-red-400/70 bg-red-500/5"
                      : isAnchor
                      ? "border-green-400/80 bg-green-400/5"
                      : "border-border bg-panel"
                  }`}
                >
                  <div className="flex justify-between gap-2">
                    <div className="font-medium truncate">
                      {item.category || item.outfit_part || "item"}
                    </div>
                    {item.outfit_part && (
                      <span className="text-[10px] text-text-muted">
                        {item.outfit_part}
                      </span>
                    )}
                  </div>

                  {item.image_url && (
                    <img
                      className="mt-1 w-full h-20 object-cover rounded-xl"
                      src={imageSrc(item)}
                      alt={item.category || item.outfit_part || "item"}
                      loading="lazy"
                    />
                  )}

                  <div className="mt-1 text-[11px] text-text-muted">
                    {(item.primary_color || "unknown")} · {(item.formality || "n/a")} · {(item.season || "n/a")}
                  </div>

                  <div className="mt-2 flex gap-1">
                    <button
                      type="button"
                      className={`flex-1 rounded-xl px-2 py-1 text-[11px] border ${
                        isAnchor ? "bg-green-400/80 text-black border-transparent" : "border-border"
                      }`}
                      onClick={() => toggleAnchor(item.id)}
                    >
                      include
                    </button>
                    <button
                      type="button"
                      className={`flex-1 rounded-xl px-2 py-1 text-[11px] border ${
                        isExcluded ? "bg-red-400/80 text-black border-transparent" : "border-border"
                      }`}
                      onClick={() => toggleExclude(item.id)}
                    >
                      exclude
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}


      {err && <div className="mt-4 text-red-400">{err}</div>}

      {suggestion && (
        <div className="mt-8">
          <h2 className="text-lg font-medium mb-3">Suggestion</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {["top", "bottom", "outer", "shoes"].map((part) => {
              const it = suggestion[part];
              return (
                <div key={part} className="card p-4">
                  <div className="text-sm text-text-muted">{part}</div>
                  {it ? (
                    <>
                      {it.image_url ? (
                        <img
                          className="mt-2 w-full h-40 object-cover rounded-xl"
                          src={imageSrc(it)}
                          alt={it.category || it.outfit_part || part}
                          loading="lazy"
                        />
                      ) : (
                        <div className="mt-2 w-full h-40 rounded-xl bg-panel border border-border grid place-items-center">
                          <span className="text-text-muted text-sm">no image</span>
                        </div>
                      )}
                      <div className="mt-2 text-sm">{it.category || it.outfit_part || "item"}</div>
                      <div className="text-xs text-text-muted">
                        {(it.primary_color || "unknown")} · {(it.formality || "n/a")} · {(it.season || "n/a")}
                      </div>
                    </>
                  ) : (
                    <div className="mt-2 w-full h-40 rounded-xl bg-panel border border-border grid place-items-center opacity-60">
                      <span className="text-text-muted text-sm">—</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
