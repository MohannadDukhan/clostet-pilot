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

const FORMALITY = [
  { value: "any", label: "Any Occasion" },
  { value: "casual", label: "Casual" },
  { value: "smart_casual", label: "Smart Casual" },
  { value: "semi_formal", label: "Semi Formal" },
  { value: "formal", label: "Formal" },
];


export default function GenerateOutfit() {
  // user state (self-managed)
  const [users, setUsers] = useState([]);
  const [userId, setUserId] = useState(null);

  const [items, setItems] = useState([]);
  const [anchorIds, setAnchorIds] = useState([]);
  const [excludeIds, setExcludeIds] = useState([]);

  const hasTop = items.some(
    (it) => it.outfit_part === "top" || it.outfit_part === "dress"
  );
  const hasBottom = items.some(
    (it) => it.outfit_part === "bottom" || it.outfit_part === "onepiece"
  );
  const hasCorePieces = hasTop && hasBottom;


  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [formality, setFormality] = useState("any");
  const [outfitDate, setOutfitDate] = useState("");

  const [suggestion, setSuggestion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [swappingPart, setSwappingPart] = useState(null);
  const [outfitIndex, setOutfitIndex] = useState(0);


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

  // Set default date to today
  useEffect(() => {
    if (!outfitDate) {
      const today = new Date().toISOString().split('T')[0];
      setOutfitDate(today);
    }
  }, [outfitDate]);

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

  function openGenerateModal() {
    if (!userId) {
      setErr("Select a user first");
      return;
    }
    setShowModal(true);
    setErr("");
  }

  async function handleSwap(part) {
    if (!suggestion || !userId) return;

    // current outfit from the ranked list
    const currentEntry = suggestion.outfits?.[outfitIndex];
    const outfit = currentEntry?.outfit || suggestion.outfit || suggestion;
    const current = outfit[part];
    if (!current) return;

    // anchor the other parts so only this one can change
    const otherParts = ["top", "bottom", "outer", "shoes"].filter(
      (p) => p !== part
    );

    const anchorFromOutfit = otherParts
      .map((p) => outfit[p]?.id)
      .filter(Boolean);

    // combine existing anchors / excludes from the UI with our new ones
    const anchorParam = Array.from(
      new Set([...(anchorIds || []), ...anchorFromOutfit])
    );
    const excludeParam = Array.from(
      new Set([...(excludeIds || []), current.id])
    );

    const params = {
      formality,
      outfit_date: outfitDate,
    };

    if (anchorParam.length) params.anchor_ids = anchorParam.join(",");
    if (excludeParam.length) params.exclude_ids = excludeParam.join(",");

    setSwappingPart(part);
    setErr("");

    try {
      const data = await suggestOutfit(userId, params);
      setSuggestion(data);
      setOutfitIndex(0);
    } catch (e) {
      console.error("swap failed", e);
      setErr("Could not swap this item. Please try again.");
    } finally {
      setSwappingPart(null);
    }
  }


  async function handleGenerateSubmit(e) {
    e.preventDefault();
    if (!userId || !outfitDate) {
      setErr("Please select date");
      return;
    }


    setLoading(true);
    setErr("");
    setShowModal(false);

    try {
      const params = { formality, outfit_date: outfitDate };

      if (anchorIds.length) {
        params.anchor_ids = anchorIds.join(",");
      }
      if (excludeIds.length) {
        params.exclude_ids = excludeIds.join(",");
      }

      const data = await suggestOutfit(userId, params);
      setSuggestion(data);
      setOutfitIndex(0);
    } catch (error) {
      setErr("Failed to generate outfit. Make sure you have items uploaded and city is set.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-8">
      <h1 className="text-2xl font-semibold">Outfit Generator</h1>
      <p className="text-text-muted mt-1">AI-powered weather-based outfit suggestions</p>

      {/* User Selection */}
      <div className="mt-6 card p-6">
        <label className="text-sm text-text-muted">Select User</label>
        <select
          className="mt-2 w-full bg-panel border border-border rounded-xl p-3 text-lg"
          value={userId ?? ""}
          onChange={(e) => setUserId(e.target.value ? Number(e.target.value) : null)}
        >
          {!users.length && <option value="">No users</option>}
          {users.map(u => (
            <option key={u.id} value={u.id}>{u.name} • {u.city}</option>
          ))}
        </select>
      </div>

      {/* Generate Button */}
      <div className="mt-6 flex justify-center">
        <button
          className="rounded-3xl px-12 py-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold text-lg shadow-lg transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          onClick={openGenerateModal}
          disabled={!userId || loading}
        >
          {loading ? "Generating..." : "✨ Generate Outfit"}
        </button>
      </div>

      {/* Interactive Modal */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowModal(false)}
        >
          <div
            className="bg-panel border border-border rounded-3xl p-8 max-w-md w-full shadow-2xl animate-fadeIn"
            onClick={(e) => e.stopPropagation()}
            style={{ animation: "bounceIn 0.5s ease-out" }}
          >
            <h2 className="text-2xl font-bold mb-2">Plan Your Outfit</h2>
            <p className="text-text-muted mb-6">Tell us about your day</p>

            <form onSubmit={handleGenerateSubmit} className="space-y-6">
              {!hasCorePieces && (
                <div className="text-xs text-amber-200 bg-amber-500/10 border border-amber-500/40 rounded-xl px-3 py-2">
                  You need at least one top and one bottom in your wardrobe to generate an outfit.
                  Try uploading a few more pieces first.
                </div>
              )}
              {/* Date Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">📅 When are you going?</label>
                <input
                  type="date"
                  className="w-full bg-background border border-border rounded-xl p-3 text-lg"
                  value={outfitDate}
                  onChange={(e) => setOutfitDate(e.target.value)}
                  required
                />
              </div>

              {/* Formality Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">👔 What's the occasion?</label>
                <div className="grid grid-cols-1 gap-2">
                  {FORMALITY.map(f => (
                    <button
                      key={f.value}
                      type="button"
                      className={`p-3 rounded-xl border-2 transition-all ${formality === f.value
                        ? "border-purple-500 bg-purple-500/10 font-semibold"
                        : "border-border hover:border-purple-300"
                        }`}
                      onClick={() => setFormality(f.value)}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  className="flex-1 px-4 py-3 rounded-xl border border-border hover:bg-panel/50 transition"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!hasCorePieces || loading}
                  className={
                    "flex-1 px-4 py-3 rounded-xl text-white font-semibold transition " +
                    (!hasCorePieces || loading
                      ? "bg-gradient-to-r from-purple-500/40 to-pink-500/40 opacity-60 cursor-not-allowed"
                      : "bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                    )
                  }
                >
                  Generate
                </button>

              </div>
            </form>
          </div>
        </div>
      )}

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
                  className={`rounded-2xl border p-2 text-xs ${isExcluded
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
                      className={`flex-1 rounded-xl px-2 py-1 text-[11px] border ${isAnchor ? "bg-green-400/80 text-black border-transparent" : "border-border"
                        }`}
                      onClick={() => toggleAnchor(item.id)}
                    >
                      include
                    </button>
                    <button
                      type="button"
                      className={`flex-1 rounded-xl px-2 py-1 text-[11px] border ${isExcluded ? "bg-red-400/80 text-black border-transparent" : "border-border"
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

      {userId && items.length === 0 && (
        <div className="mt-6 card p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-sm font-medium">No items in your wardrobe yet</h2>
            <p className="text-xs text-text-muted mt-1">
              Upload at least one top and one bottom so we can start building outfits around your clothes.
            </p>
          </div>
          <a href="/upload" className="btn btn-accent text-xs">
            Upload items
          </a>
        </div>
      )}



      {err && (
        <div className="mt-6 card p-4 bg-red-500/10 border-red-400/50">
          <p className="text-red-400">{err}</p>
        </div>
      )}

      {/* Beautiful Outfit Display */}
      {suggestion && (() => {
        const totalOutfits = suggestion.outfits?.length || 0;
        const currentEntry = suggestion.outfits?.[outfitIndex];
        const outfit = currentEntry?.outfit || suggestion.outfit || suggestion;
        const score = currentEntry?.score;
        const rankEmoji = ["🥇", "🥈", "🥉"][outfitIndex] || `#${outfitIndex + 1}`;

        return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="bg-gradient-to-br from-panel to-background border border-border rounded-3xl p-8 max-w-4xl w-full shadow-2xl max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="flex items-center justify-center gap-3 mb-1">
                <span className="text-2xl">{rankEmoji}</span>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Outfit {outfitIndex + 1} of {totalOutfits}
                </h2>
              </div>
              {score != null && (
                <div className="mt-2 inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30">
                  <span className="text-sm text-text-muted">ML Score</span>
                  <span className="text-lg font-bold text-purple-400">{score}/10</span>
                </div>
              )}
              {/* Weather summary */}
              {suggestion.weather && (
                <div className="mt-3 text-sm text-text-muted flex flex-col items-center gap-1">
                  <div>
                    <span className="font-medium">
                      {suggestion.weather.city || "Your city"}
                    </span>{" "}
                    · {suggestion.weather.temperature}°C
                    {" "}
                    <span className="text-xs text-text-muted">
                      ({suggestion.weather.temp_min}–{suggestion.weather.temp_max}°C)
                    </span>
                  </div>
                  <div className="text-xs uppercase tracking-wide">
                    season bucket:{" "}
                    <span className="font-semibold">
                      {suggestion.weather.season}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Outfit Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
              {["outer", "top", "bottom", "shoes"].map((part) => {
                const it = outfit[part];

                // Skip outer if it's empty
                if (part === "outer" && !it) return null;

                return (
                  <div
                    key={part}
                    className="relative group"
                    style={{ animation: `bounceIn 0.6s ease-out ${part === "outer" ? "0s" : part === "top" ? "0.1s" : part === "bottom" ? "0.2s" : "0.3s"}` }}
                  >
                    <div className="card p-4 hover:shadow-xl transition-shadow">
                      <div className="text-sm font-medium text-text-muted mb-3 capitalize flex items-center gap-2">
                        {part === "top" && "👕"}
                        {part === "bottom" && "👖"}
                        {part === "outer" && "🧥"}
                        {part === "shoes" && "👟"}
                        {part}
                      </div>

                      {it ? (
                        <>
                          {it.image_url ? (
                            <div className="relative">
                              <img
                                className="w-full h-48 object-cover rounded-2xl shadow-md"
                                src={imageSrc(it)}
                                alt={it.category || it.outfit_part || part}
                                loading="lazy"
                              />
                              <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                          ) : (
                            <div className="w-full h-48 rounded-2xl bg-panel border-2 border-dashed border-border grid place-items-center">
                              <span className="text-text-muted text-sm">No image</span>
                            </div>
                          )}
                          <div className="mt-3">
                            <div className="font-semibold text-base capitalize">
                              {it.category || it.outfit_part || "item"}
                            </div>
                            <div className="text-xs text-text-muted mt-1 space-y-0.5">
                              <div>🎨 {it.primary_color || "unknown"}</div>
                              {it.formality && it.formality !== "any" && (
                                <div>👔 {it.formality}</div>
                              )}
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() => handleSwap(part)}
                            className="mt-3 inline-flex items-center justify-center rounded-full border border-accent/70 px-3 py-1 text-[11px] uppercase tracking-wide text-accent hover:bg-accent/10 transition"
                            disabled={swappingPart === part}
                          >
                            {swappingPart === part ? "Swapping..." : "Swap this piece"}
                          </button>
                        </>
                      ) : (
                        <div className="w-full h-48 rounded-2xl bg-panel/50 border-2 border-dashed border-border/50 grid place-items-center opacity-40">
                          <span className="text-text-muted text-sm">—</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Dot indicators */}
            {totalOutfits > 1 && (
              <div className="flex justify-center gap-2 mb-6">
                {suggestion.outfits.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setOutfitIndex(idx)}
                    className={`w-3 h-3 rounded-full transition-all ${
                      idx === outfitIndex
                        ? "bg-purple-500 scale-125"
                        : "bg-border hover:bg-purple-400/50"
                    }`}
                  />
                ))}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4 justify-center flex-wrap">
              <button
                className="px-8 py-3 rounded-2xl border border-border hover:bg-panel transition"
                onClick={() => { setSuggestion(null); setOutfitIndex(0); }}
              >
                Close
              </button>

              {totalOutfits > 1 && outfitIndex < totalOutfits - 1 && (
                <button
                  className="px-8 py-3 rounded-2xl bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold transition"
                  onClick={() => setOutfitIndex((i) => i + 1)}
                >
                  Next Outfit →
                </button>
              )}

              <button
                className="px-8 py-3 rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold transition"
                onClick={() => {
                  setSuggestion(null);
                  setOutfitIndex(0);
                  openGenerateModal();
                }}
              >
                Generate New
              </button>
            </div>
          </div>
        </div>
        );
      })()}
    </div>
  );
}
