import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { API, listUserItems, scoreOutfit } from "../api";

function imageSrc(item) {
  const url = item?.image_url || "";
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  const base = (API?.defaults?.baseURL || "").replace(/\/$/, "");
  const path = url.startsWith("/storage") ? url : `/storage/${url}`;
  return `${base}${path}`;
}

const SLOTS = [
  { key: "top",    label: "Top",       icon: "👕", part: "top" },
  { key: "bottom", label: "Bottom",    icon: "👖", part: "bottom" },
  { key: "outer",  label: "Outerwear", icon: "🧥", part: "outerwear" },
  { key: "shoes",  label: "Shoes",     icon: "👟", part: "shoes" },
];

function getUser() {
  try {
    const raw = localStorage.getItem("cp:user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function ScoreGauge({ score }) {
  const pct = Math.max(0, Math.min(score / 10, 1)) * 100;
  const hue = (pct / 100) * 120;
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-40 h-40">
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
          <circle cx="60" cy="60" r="52" fill="none" stroke="currentColor"
            className="text-border" strokeWidth="10" />
          <circle cx="60" cy="60" r="52" fill="none"
            stroke={`hsl(${hue}, 80%, 55%)`} strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${pct * 3.267} 326.7`}
            style={{ transition: "stroke-dasharray 0.8s ease, stroke 0.8s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold" style={{ color: `hsl(${hue}, 80%, 55%)` }}>
            {score}
          </span>
          <span className="text-xs text-text-muted">/10</span>
        </div>
      </div>
    </div>
  );
}

function VerdictBadge({ verdict }) {
  if (!verdict) return null;
  const bg = {
    green: "bg-green-500/15 border-green-500/40 text-green-400",
    blue: "bg-blue-500/15 border-blue-500/40 text-blue-400",
    yellow: "bg-yellow-500/15 border-yellow-500/40 text-yellow-400",
    orange: "bg-orange-500/15 border-orange-500/40 text-orange-400",
    red: "bg-red-500/15 border-red-500/40 text-red-400",
  }[verdict.color] || "bg-panel border-border text-text";
  return (
    <span className={`inline-flex items-center gap-2 px-5 py-2 rounded-full border text-lg font-semibold ${bg}`}>
      <span className="text-2xl">{verdict.emoji}</span>
      {verdict.label}
    </span>
  );
}

function FeatureBar({ label, value, max, unit = "", info }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="group">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-text-muted">{label}</span>
        <span className="font-mono">{typeof value === "number" ? (Number.isInteger(value) ? value : value.toFixed(1)) : value}{unit}</span>
      </div>
      <div className="h-2 bg-border rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, #4ade80, #3b82f6)` }} />
      </div>
      {info && <p className="text-[10px] text-text-muted mt-0.5 opacity-0 group-hover:opacity-100 transition">{info}</p>}
    </div>
  );
}

export default function StyleLab() {
  const navigate = useNavigate();
  const user = getUser();
  const userId = user?.id ?? null;

  const [items, setItems] = useState([]);
  const [picks, setPicks] = useState({ top: null, bottom: null, outer: null, shoes: null });
  const [openSlot, setOpenSlot] = useState(null);
  const [result, setResult] = useState(null);
  const [scoring, setScoring] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!user) {
      navigate("/login", { replace: true });
    }
  }, []);

  useEffect(() => {
    if (!userId) { setItems([]); return; }
    (async () => {
      try {
        const data = await listUserItems(userId);
        setItems(data || []);
        setPicks({ top: null, bottom: null, outer: null, shoes: null });
        setResult(null);
      } catch {
        console.error("Failed to load items");
      }
    })();
  }, [userId]);

  const itemsByPart = (partFilter) =>
    items.filter((i) => i.outfit_part === partFilter);

  const pickedItem = (slotKey) => {
    const id = picks[slotKey];
    return id ? items.find((i) => i.id === id) : null;
  };

  const filledCount = Object.values(picks).filter(Boolean).length;

  const doScore = useCallback(async () => {
    if (!userId) return;
    if (!picks.top && !picks.bottom) { setResult(null); return; }
    setScoring(true);
    setErr("");
    try {
      const data = await scoreOutfit(userId, {
        top_id: picks.top || undefined,
        bottom_id: picks.bottom || undefined,
        outer_id: picks.outer || undefined,
        shoes_id: picks.shoes || undefined,
      });
      setResult(data);
    } catch (e) {
      console.error("Score failed", e);
      setErr(e?.response?.data?.detail || "Scoring failed");
      setResult(null);
    } finally {
      setScoring(false);
    }
  }, [userId, picks]);

  useEffect(() => {
    if (picks.top || picks.bottom) {
      const timer = setTimeout(doScore, 300);
      return () => clearTimeout(timer);
    } else {
      setResult(null);
    }
  }, [picks, doScore]);

  if (!user) return null;

  function selectItem(slotKey, itemId) {
    setPicks((prev) => ({ ...prev, [slotKey]: prev[slotKey] === itemId ? null : itemId }));
    setOpenSlot(null);
  }

  function clearSlot(slotKey) {
    setPicks((prev) => ({ ...prev, [slotKey]: null }));
  }

  function clearAll() {
    setPicks({ top: null, bottom: null, outer: null, shoes: null });
    setResult(null);
  }

  function randomize() {
    const rnd = (part) => {
      const pool = itemsByPart(part);
      return pool.length ? pool[Math.floor(Math.random() * pool.length)].id : null;
    };
    setPicks({ top: rnd("top"), bottom: rnd("bottom"), outer: rnd("outerwear"), shoes: rnd("shoes") });
  }

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            🧪 Style Lab
          </h1>
          <p className="text-text-muted mt-1 text-sm">
            Pick pieces from your wardrobe & see how they score together. Experiment freely!
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT: Item Slots */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex gap-2 mb-2">
            <button onClick={randomize}
              className="btn text-xs gap-1.5" disabled={items.length < 2}>
              🎲 Random
            </button>
            <button onClick={clearAll}
              className="btn text-xs gap-1.5" disabled={filledCount === 0}>
              🗑️ Clear All
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {SLOTS.map(({ key, label, icon, part }) => {
              const item = pickedItem(key);
              const isOpen = openSlot === key;
              const pool = itemsByPart(part);
              const clashSlots = result?.explanations
                ?.filter((e) => e.type === "clash" || e.type === "tension")
                .flatMap((e) => e.slots || []) || [];
              const isClashing = clashSlots.includes(key === "outer" ? "outerwear" : key);

              return (
                <div key={key} className="relative">
                  <div
                    className={`card p-3 cursor-pointer transition-all hover:shadow-lg group ${
                      isClashing ? "ring-2 ring-red-400/60" : ""
                    } ${item ? "" : "border-dashed border-2"}`}
                    onClick={() => setOpenSlot(isOpen ? null : key)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium flex items-center gap-1.5">
                        {icon} {label}
                      </span>
                      {item && (
                        <button
                          onClick={(e) => { e.stopPropagation(); clearSlot(key); }}
                          className="text-text-muted hover:text-red-400 text-xs transition"
                          title="Remove"
                        >✕</button>
                      )}
                    </div>

                    {item ? (
                      <>
                        {item.image_url ? (
                          <img
                            src={imageSrc(item)}
                            alt={item.category || label}
                            className="w-full h-36 object-cover rounded-xl"
                            loading="lazy"
                          />
                        ) : (
                          <div className="w-full h-36 rounded-xl bg-surface grid place-items-center text-text-muted text-xs">
                            No image
                          </div>
                        )}
                        <div className="mt-2">
                          <div className="text-sm font-medium truncate capitalize">
                            {item.category || item.outfit_part}
                          </div>
                          <div className="flex items-center gap-1.5 mt-1">
                            {item.primary_color_hex && (
                              <span
                                className="w-3.5 h-3.5 rounded-full border border-white/20 shrink-0"
                                style={{ backgroundColor: item.primary_color_hex }}
                              />
                            )}
                            <span className="text-xs text-text-muted capitalize">
                              {item.primary_color || "unknown"}
                            </span>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="w-full h-36 rounded-xl bg-surface/50 grid place-items-center">
                        <div className="text-center text-text-muted">
                          <div className="text-3xl mb-1 opacity-30">+</div>
                          <div className="text-xs">Tap to pick</div>
                        </div>
                      </div>
                    )}
                  </div>

                  {isOpen && (
                    <div className="absolute z-40 top-full left-0 right-0 mt-2 max-h-72 overflow-y-auto bg-panel border border-border rounded-2xl shadow-2xl p-2 animate-fadeIn"
                      style={{ minWidth: "100%" }}>
                      {pool.length === 0 ? (
                        <p className="text-xs text-text-muted p-3 text-center">
                          No {label.toLowerCase()} items in wardrobe
                        </p>
                      ) : (
                        <div className="grid grid-cols-2 gap-2">
                          {pool.map((it) => (
                            <button
                              key={it.id}
                              onClick={() => selectItem(key, it.id)}
                              className={`rounded-xl border p-1.5 text-left transition hover:border-accent/60 ${
                                picks[key] === it.id
                                  ? "border-accent bg-accent/10"
                                  : "border-border"
                              }`}
                            >
                              {it.image_url ? (
                                <img
                                  src={imageSrc(it)}
                                  alt={it.category}
                                  className="w-full h-20 object-cover rounded-lg"
                                  loading="lazy"
                                />
                              ) : (
                                <div className="w-full h-20 rounded-lg bg-surface grid place-items-center text-[10px] text-text-muted">
                                  No img
                                </div>
                              )}
                              <div className="mt-1 px-0.5">
                                <div className="text-[11px] font-medium truncate capitalize">
                                  {it.category || it.outfit_part}
                                </div>
                                <div className="flex items-center gap-1 mt-0.5">
                                  {it.primary_color_hex && (
                                    <span
                                      className="w-2.5 h-2.5 rounded-full border border-white/20"
                                      style={{ backgroundColor: it.primary_color_hex }}
                                    />
                                  )}
                                  <span className="text-[10px] text-text-muted capitalize">
                                    {it.primary_color || "?"}
                                  </span>
                                </div>
                              </div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {openSlot && (
            <div className="fixed inset-0 z-30" onClick={() => setOpenSlot(null)} />
          )}
        </div>

        {/* RIGHT: Score Panel */}
        <div className="space-y-4">
          {scoring && (
            <div className="card p-8 flex flex-col items-center justify-center gap-3 animate-pulse">
              <div className="w-16 h-16 rounded-full border-4 border-border border-t-purple-500 animate-spin" />
              <span className="text-sm text-text-muted">Analyzing colors…</span>
            </div>
          )}

          {!scoring && result && (
            <div className="card p-6 space-y-6 animate-fadeIn">
              <div className="flex flex-col items-center gap-3">
                <ScoreGauge score={result.score} />
                <VerdictBadge verdict={result.verdict} />
              </div>

              <div className="space-y-2.5">
                <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wide">Analysis</h3>
                {result.explanations?.map((ex, i) => (
                  <div
                    key={i}
                    className={`rounded-xl p-3 text-sm border ${
                      ex.type === "clash"
                        ? "bg-red-500/8 border-red-500/30"
                        : ex.type === "tension"
                        ? "bg-orange-500/8 border-orange-500/30"
                        : ex.type === "loud"
                        ? "bg-yellow-500/8 border-yellow-500/30"
                        : "bg-green-500/8 border-green-500/30"
                    }`}
                  >
                    <span className="mr-1.5">{ex.icon}</span>
                    {ex.message}
                  </div>
                ))}
              </div>

              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wide">Feature Breakdown</h3>
                <FeatureBar label="Avg Hue Distance" value={result.features.avg_hue_distance} max={180} unit="°" info="Lower is more harmonious. Under 40° = analogous, 150°+ = clashing" />
                <FeatureBar label="Max Hue Distance" value={result.features.max_hue_distance} max={180} unit="°" info="Worst pair hue clash. >120° usually means visible color tension" />
                <FeatureBar label="Avg Saturation" value={result.features.avg_saturation} max={100} info="Below 30 = muted/neutral palette, above 60 = very colorful" />
                <FeatureBar label="Loud Pieces (S≥60)" value={result.features.high_sat_count} max={4} info="Highly saturated garments. Best outfits have 0-1 loud pieces" />
                <FeatureBar label="Neutral Anchors (S<20)" value={result.features.neutral_count} max={4} info="Black, white, gray pieces that ground the outfit" />
                <div className="flex items-center justify-between text-xs">
                  <span className="text-text-muted">Light/Dark Contrast</span>
                  <span className={`font-semibold ${result.features.has_contrast ? "text-green-400" : "text-text-muted"}`}>
                    {result.features.has_contrast ? "✓ Yes" : "✗ No"}
                  </span>
                </div>
              </div>

              {!result.used_ml && (
                <p className="text-[11px] text-yellow-400/70 text-center mt-2">
                  ⚠ Used rule-based fallback (missing HSV on some pieces)
                </p>
              )}
            </div>
          )}

          {!scoring && !result && (
            <div className="card p-8 flex flex-col items-center justify-center gap-3 text-center">
              <div className="text-5xl opacity-20">🎨</div>
              <p className="text-text-muted text-sm">
                Pick at least a <strong>top</strong> and <strong>bottom</strong> to see the score
              </p>
            </div>
          )}
        </div>
      </div>

      {err && (
        <div className="mt-6 card p-4 bg-red-500/10 border-red-400/50">
          <p className="text-red-400 text-sm">{err}</p>
        </div>
      )}
    </div>
  );
}
