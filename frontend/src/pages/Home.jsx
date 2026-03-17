import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Container from "../components/Container";
import { API, listUserItems, imageSrc } from "../api";

// ── Content card — subtle fill + hover ────────────────────────────────────
function Card({ className = "", children }) {
  return (
    <div
      className={`rounded-xl border border-white/10 bg-white/[0.08] p-5 transition-colors duration-200 hover:border-white/20 hover:bg-white/[0.12] ${className}`}
    >
      {children}
    </div>
  );
}

// ── Frosted glass card (hero preview + modal) ─────────────────────────────
function GlassCard({ className = "", children, onClick }) {
  return (
    <div
      onClick={onClick}
      className={`rounded-2xl border border-white/12 bg-white/[0.10] backdrop-blur-md ${onClick ? "cursor-pointer" : ""} ${className}`}
    >
      {children}
    </div>
  );
}

// ── Section container — light presence for major sections ─────────────────
function Section({ id, className = "", children }) {
  return (
    <section
      id={id}
      className={`rounded-2xl border border-white/[0.09] bg-white/[0.05] px-6 py-10 md:px-10 md:py-14 ${className}`}
    >
      {children}
    </section>
  );
}

// ── Section heading ───────────────────────────────────────────────────────
function SectionHeading({ eyebrow, title, subtitle }) {
  return (
    <div className="max-w-3xl space-y-3">
      <p className="text-xs font-medium uppercase tracking-[0.22em] text-accent/70">
        {eyebrow}
      </p>
      <h2 className="text-2xl font-semibold tracking-tight md:text-4xl">{title}</h2>
      {subtitle ? (
        <p className="text-[15px] leading-relaxed text-text-muted">{subtitle}</p>
      ) : null}
    </div>
  );
}

// ── Thin divider ──────────────────────────────────────────────────────────
function SectionDivider() {
  return (
    <div className="h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />
  );
}

// ── SVG icons ─────────────────────────────────────────────────────────────
function Icon({ name, className = "h-5 w-5" }) {
  const base = `stroke-current fill-none ${className}`;
  if (name === "upload")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M12 16V4" /><path d="M8 8l4-4 4 4" />
        <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
      </svg>
    );
  if (name === "ai")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <rect x="5" y="5" width="14" height="14" rx="3" />
        <path d="M9 9h6v6H9z" />
        <path d="M3 10h2M3 14h2M19 10h2M19 14h2M10 3v2M14 3v2M10 19v2M14 19v2" />
      </svg>
    );
  if (name === "wardrobe")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12H4z" />
        <path d="M12 4v14" /><path d="M9 10h.01M15 10h.01" />
      </svg>
    );
  if (name === "weather")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M6 15a4 4 0 0 1 2.6-7A5 5 0 0 1 18 10a3 3 0 1 1 0 6H6z" />
        <path d="M8 19l-1 2M12 19l-1 2M16 19l-1 2" />
      </svg>
    );
  if (name === "vision")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <rect x="3" y="4" width="18" height="14" rx="2" />
        <path d="M8 14l3-3 3 2 3-4" /><circle cx="9" cy="9" r="1" />
      </svg>
    );
  if (name === "meteo")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M12 3v3M5.6 5.6l2.1 2.1M3 12h3M5.6 18.4l2.1-2.1M12 18a6 6 0 1 0 0-12" />
      </svg>
    );
  if (name === "rules")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M8 6h11M8 12h11M8 18h11" /><path d="M3 6h.01M3 12h.01M3 18h.01" />
      </svg>
    );
  if (name === "swap")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M7 7h10l-3-3" /><path d="M17 17H7l3 3" />
      </svg>
    );
  if (name === "bulk")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <rect x="3" y="7" width="8" height="8" rx="1" />
        <rect x="13" y="7" width="8" height="8" rx="1" />
        <path d="M7 15v3h10v-3" />
      </svg>
    );
  if (name === "edit")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M4 20h4l10-10-4-4L4 16v4z" /><path d="M12 6l4 4" />
      </svg>
    );
  if (name === "arrow")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M5 12h14" /><path d="M15 7l5 5-5 5" />
      </svg>
    );
  if (name === "check")
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="2" aria-hidden="true">
        <path d="M6 12l4 4 8-8" />
      </svg>
    );
  return null;
}

// ── Card icon — light accent tint ─────────────────────────────────────────
function CardIcon({ name }) {
  return (
    <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg border border-accent/25 bg-accent/10 text-accent/80">
      <Icon name={name} className="h-5 w-5" />
    </div>
  );
}

// ── Wardrobe preview — real item images with empty-state fallback ──────────
function WardrobePreview({ items }) {
  const navigate = useNavigate();
  const displayItems = (items || []).slice(0, 15);
  const hasItems = displayItems.length > 0;

  return (
    <GlassCard
      className="flex flex-col p-5 md:p-7 transition-all duration-200 hover:border-white/24 hover:scale-[1.01]"
      onClick={() => navigate("/dashboard")}
    >
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm font-semibold tracking-wide text-accent">Your wardrobe</p>
        {hasItems && (
          <span className="rounded-full border border-white/12 px-2.5 py-0.5 text-[11px] text-text-muted">
            {items.length} {items.length === 1 ? "item" : "items"}
          </span>
        )}
      </div>

      {/* Grid or empty state */}
      {hasItems ? (
        <div className="grid grid-cols-4 gap-2 sm:grid-cols-5">
          {displayItems.map((item) => (
            <div
              key={item.id}
              className="aspect-square overflow-hidden rounded-lg border border-white/8 bg-white/[0.06]"
            >
              <img
                src={imageSrc(item)}
                alt={item.category || item.outfit_part || "item"}
                className="h-full w-full object-cover transition-transform duration-300 hover:scale-105"
                loading="lazy"
              />
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
          <p className="text-base font-semibold">Your wardrobe is empty</p>
          <p className="max-w-xs text-sm text-text-muted">
            Upload your first items to start generating outfits.
          </p>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); navigate("/upload"); }}
            className="mt-1 inline-flex items-center justify-center rounded-xl bg-accent px-5 py-2 text-sm font-semibold text-bg transition-opacity hover:opacity-90"
          >
            Upload Items
          </button>
        </div>
      )}

      {/* Footer label */}
      {hasItems && (
        <p className="mt-4 text-xs text-text-muted">
          {`${displayItems.length} piece${displayItems.length !== 1 ? "s" : ""} · AI-labeled and generation-ready`}
        </p>
      )}
    </GlassCard>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────
export default function Home() {
  const navigate = useNavigate();
  const [openFaqIndex, setOpenFaqIndex] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [wardrobeItems, setWardrobeItems] = useState([]);
  const [analyzeOpen, setAnalyzeOpen] = useState(false);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [analyzeError, setAnalyzeError] = useState("");
  const [analyzeResults, setAnalyzeResults] = useState([]);

  // Sync active user from localStorage
  useEffect(() => {
    const sync = () => {
      try {
        const raw = localStorage.getItem("cp:user");
        const parsed = raw ? JSON.parse(raw) : null;
        setSelectedUserId(parsed?.id ? Number(parsed.id) : null);
      } catch {
        setSelectedUserId(null);
      }
    };
    sync();
    window.addEventListener("storage", sync);
    window.addEventListener("focus", sync);
    return () => {
      window.removeEventListener("storage", sync);
      window.removeEventListener("focus", sync);
    };
  }, []);

  // Fetch wardrobe items for the hero preview whenever user changes
  useEffect(() => {
    if (!selectedUserId) {
      setWardrobeItems([]);
      return;
    }
    listUserItems(selectedUserId)
      .then((data) => setWardrobeItems(data || []))
      .catch(() => setWardrobeItems([]));
  }, [selectedUserId]);

  const goToHowItWorks = () => {
    document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleGetStarted = () => {
    let hasUser = false;
    try {
      const parsed = JSON.parse(localStorage.getItem("cp:user") || "null");
      hasUser = Boolean(parsed?.id);
    } catch { /**/ }
    navigate(hasUser ? "/dashboard" : "/create-user");
  };

  const handleAnalyzeWardrobe = async () => {
    if (!selectedUserId) return;
    setAnalyzeOpen(true);
    setAnalyzeLoading(true);
    setAnalyzeError("");
    setAnalyzeResults([]);
    try {
      const { data } = await API.get(`/users/${selectedUserId}/wardrobe/recommendations`);
      setAnalyzeResults(Array.isArray(data?.recommendations) ? data.recommendations : []);
    } catch {
      setAnalyzeError("Could not analyze wardrobe right now. Please try again.");
    } finally {
      setAnalyzeLoading(false);
    }
  };

  return (
    <div className="relative overflow-hidden">
      {/* ── Subtle background depth — no neon, just cool neutral orbs ──── */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-48 -top-40 h-[32rem] w-[32rem] rounded-full bg-[radial-gradient(circle,rgba(90,110,160,0.14)_0%,transparent_68%)] blur-3xl" />
        <div className="absolute -right-40 -top-32 h-[28rem] w-[28rem] rounded-full bg-[radial-gradient(circle,rgba(110,90,160,0.10)_0%,transparent_70%)] blur-3xl" />
        <div className="absolute bottom-0 left-1/2 h-[20rem] w-[40rem] -translate-x-1/2 rounded-full bg-[radial-gradient(circle,rgba(74,222,128,0.04)_0%,transparent_70%)] blur-3xl" />
      </div>

      <Container className="relative z-10 space-y-6 pb-16 md:space-y-8">

        {/* ── Hero ─────────────────────────────────────────────────────── */}
        <section className="grid gap-10 pb-4 pt-12 md:pb-8 md:pt-16 lg:grid-cols-2 lg:gap-14">
          <div className="flex flex-col justify-center space-y-7">

            {/* Badge */}
            <p className="inline-flex w-fit items-center gap-2 rounded-full border border-accent/25 bg-accent/8 px-4 py-1.5 text-xs font-medium text-accent/80">
              <span className="h-1.5 w-1.5 rounded-full bg-accent/70" />
              Smart outfit planning from your real wardrobe
            </p>

            {/* Headline */}
            <h1 className="text-5xl font-bold leading-[1.05] tracking-tight md:text-6xl lg:text-7xl">
              <span className="bg-gradient-to-br from-white via-white to-white/60 bg-clip-text text-transparent">
                Outfit Maker
              </span>
            </h1>

            <p className="max-w-md text-[15px] leading-relaxed text-text-muted md:text-base">
              Digitise your wardrobe, generate weather-aware outfits with AI, and
              stop repeating the same combinations every morning.
            </p>

            {/* CTAs */}
            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={handleGetStarted}
                className="inline-flex items-center justify-center rounded-xl bg-accent px-7 py-3 font-semibold text-bg shadow-[0_4px_20px_rgba(74,222,128,0.22)] transition-all duration-200 hover:opacity-90 hover:shadow-[0_4px_28px_rgba(74,222,128,0.32)]"
              >
                Get Started
              </button>
              <button
                type="button"
                onClick={goToHowItWorks}
                className="inline-flex items-center justify-center rounded-xl border border-white/16 px-7 py-3 font-medium text-text transition-colors duration-200 hover:border-white/28 hover:bg-white/[0.05]"
              >
                How It Works
              </button>
            </div>

            {/* Micro tags */}
            <div className="flex flex-wrap gap-2">
              {MICRO_TAGS.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-text-muted"
                >
                  {tag}
                </span>
              ))}
            </div>

            {/* Wardrobe analysis shortcut (signed-in users) */}
            {selectedUserId ? (
              <button
                type="button"
                onClick={handleAnalyzeWardrobe}
                className="inline-flex w-fit items-center gap-2 rounded-xl border border-accent/30 bg-accent/8 px-5 py-2.5 text-sm font-medium text-accent transition-colors duration-200 hover:border-accent/50 hover:bg-accent/14"
              >
                <Icon name="wardrobe" className="h-4 w-4" />
                Analyze My Wardrobe
              </button>
            ) : null}
          </div>

          {/* Wardrobe preview — real images */}
          <WardrobePreview items={wardrobeItems} />
        </section>

        <SectionDivider />

        {/* ── How It Works ─────────────────────────────────────────────── */}
        <Section id="how-it-works" className="space-y-8">
          <SectionHeading
            eyebrow="How It Works"
            title="From Closet Photos To Complete Outfits"
            subtitle="A clear four-step workflow that turns your wardrobe photos into reliable, weather-aware recommendations."
          />

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {HOW_IT_WORKS_STEPS.map((step, i) => (
              <Card key={step.title}>
                <CardIcon name={step.icon} />
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-accent/60">
                  Step {i + 1}
                </p>
                <h3 className="mb-2 text-base font-semibold leading-snug">{step.title}</h3>
                <p className="text-sm leading-relaxed text-text-muted">{step.description}</p>
              </Card>
            ))}
          </div>
        </Section>

        {/* ── Feature Highlights ───────────────────────────────────────── */}
        <Section className="space-y-8">
          <SectionHeading
            eyebrow="Feature Highlights"
            title="Core Engine, Premium Experience"
            subtitle="Technical foundations designed for speed, clarity, and reliable outfit output."
          />

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <Card key={feature.title}>
                <CardIcon name={feature.icon} />
                <h3 className="mb-2 text-base font-semibold leading-snug">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-text-muted">{feature.description}</p>
                {feature.chips?.length ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {feature.chips.map((chip) => (
                      <span
                        key={chip}
                        className="rounded-full border border-accent/20 bg-accent/8 px-2.5 py-0.5 text-[11px] text-accent/70"
                      >
                        {chip}
                      </span>
                    ))}
                  </div>
                ) : null}
              </Card>
            ))}
          </div>
        </Section>

        {/* ── Benefits ─────────────────────────────────────────────────── */}
        <Section>
          <div className="grid gap-10 lg:grid-cols-2 lg:gap-16">
            <SectionHeading
              eyebrow="What You Get"
              title="Better Outfit Decisions, Less Daily Friction"
              subtitle="Many mornings are lost to indecision and weather misses. Outfit Maker keeps your wardrobe visible and delivers combinations that fit your day."
            />

            <div>
              <h3 className="mb-6 text-lg font-semibold">Benefits</h3>
              <ul className="space-y-4">
                {BENEFITS.map((benefit) => (
                  <li key={benefit} className="flex items-center gap-3">
                    <span className="inline-flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border border-accent/30 bg-accent/10 text-accent">
                      <Icon name="check" className="h-3.5 w-3.5" />
                    </span>
                    <span className="text-[15px] text-text-muted">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Section>

        {/* ── Demo Flow ────────────────────────────────────────────────── */}
        <Section className="space-y-8">
          <SectionHeading
            eyebrow="Demo Flow"
            title="Upload → Weather → Outfit"
            subtitle="How a single photo becomes a complete, context-aware outfit suggestion."
          />

          <div className="grid gap-4 lg:grid-cols-[1fr_auto_1fr_auto_1fr] lg:items-start">
            <Card>
              <span className="mb-3 inline-flex h-7 w-7 items-center justify-center rounded-full border border-accent/30 bg-accent/10 text-xs font-semibold text-accent">
                1
              </span>
              <p className="mb-2 font-semibold">Upload Photo</p>
              <p className="mb-4 text-sm leading-relaxed text-text-muted">
                Item is analyzed and converted to structured labels.
              </p>
              <div className="rounded-lg border border-white/10 bg-black/25 px-3 py-2.5 font-mono text-[11px] text-green-300/70">
                top · hoodie · navy · fall · casual
              </div>
            </Card>

            <div className="hidden items-start justify-center pt-16 text-white/20 lg:flex">
              <Icon name="arrow" className="h-5 w-5" />
            </div>

            <Card>
              <span className="mb-3 inline-flex h-7 w-7 items-center justify-center rounded-full border border-accent/30 bg-accent/10 text-xs font-semibold text-accent">
                2
              </span>
              <p className="mb-2 font-semibold">Weather Context</p>
              <p className="mb-4 text-sm leading-relaxed text-text-muted">
                Conditions shape layering and warmth constraints.
              </p>
              <div className="rounded-lg border border-white/10 bg-black/25 px-3 py-2.5 font-mono text-[11px] text-blue-300/70">
                4°C · cold · fall
              </div>
            </Card>

            <div className="hidden items-start justify-center pt-16 text-white/20 lg:flex">
              <Icon name="arrow" className="h-5 w-5" />
            </div>

            <Card>
              <span className="mb-3 inline-flex h-7 w-7 items-center justify-center rounded-full border border-accent/30 bg-accent/10 text-xs font-semibold text-accent">
                3
              </span>
              <p className="mb-2 font-semibold">Outfit Output</p>
              <p className="mb-4 text-sm leading-relaxed text-text-muted">
                Generated pieces appear, ready to swap or save.
              </p>
              <div className="grid grid-cols-2 gap-2 text-[11px] text-text-muted">
                {["Top: Navy Hoodie","Bottom: Black Jeans","Outer: Wool Coat","Shoes: Leather Boots"].map((label) => (
                  <div key={label} className="rounded-lg border border-white/10 bg-black/25 p-2">
                    {label}
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <p className="text-sm text-text-muted">
            If one piece is off, use swap-one-piece to replace it while keeping the rest of the outfit anchored.
          </p>
        </Section>

        {/* ── FAQ ──────────────────────────────────────────────────────── */}
        <Section className="space-y-8">
          <SectionHeading
            eyebrow="FAQ"
            title="Common Questions"
            subtitle="Quick answers about storage, controls, and generation behaviour."
          />

          <div className="divide-y divide-white/8">
            {FAQS.map((faq, index) => {
              const isOpen = openFaqIndex === index;
              return (
                <div key={faq.question}>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between gap-4 py-4 text-left transition-colors hover:text-accent/90"
                    onClick={() => setOpenFaqIndex(isOpen ? null : index)}
                  >
                    <span className="font-medium">{faq.question}</span>
                    <span className="flex-shrink-0 text-xl leading-none text-text-muted">
                      {isOpen ? "−" : "+"}
                    </span>
                  </button>
                  <div
                    className={`grid transition-all duration-300 ease-out ${
                      isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                    }`}
                  >
                    <div className="overflow-hidden pb-4 text-sm leading-relaxed text-text-muted">
                      {faq.answer}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Section>

        {/* ── CTA ──────────────────────────────────────────────────────── */}
        <section className="rounded-2xl border border-accent/20 bg-gradient-to-br from-accent/[0.08] via-transparent to-transparent px-8 py-14 text-center md:py-18">
          <p className="mb-3 text-xs font-medium uppercase tracking-[0.22em] text-accent/70">
            Get Started
          </p>
          <h3 className="text-2xl font-bold tracking-tight md:text-3xl">
            Ready to build your wardrobe?
          </h3>
          <p className="mt-3 text-sm text-text-muted">
            Outfit Maker — Capstone Project.
          </p>
          <div className="mt-7 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <button
              type="button"
              onClick={() => navigate("/upload")}
              className="inline-flex items-center justify-center rounded-xl bg-accent px-8 py-3 font-semibold text-bg shadow-[0_4px_20px_rgba(74,222,128,0.22)] transition-all duration-200 hover:opacity-90 hover:shadow-[0_4px_28px_rgba(74,222,128,0.32)]"
            >
              Upload Your First Item
            </button>
            <button
              type="button"
              onClick={handleGetStarted}
              className="inline-flex items-center justify-center rounded-xl border border-white/16 px-8 py-3 font-medium text-text transition-colors duration-200 hover:border-white/28 hover:bg-white/[0.05]"
            >
              View My Wardrobe
            </button>
          </div>
        </section>

      </Container>

      {/* ── Wardrobe analysis modal ───────────────────────────────────── */}
      {analyzeOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 py-6 backdrop-blur-sm">
          <GlassCard className="max-h-[88vh] w-full max-w-3xl overflow-y-auto p-6 md:p-8">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-accent/70">
                  Wardrobe Analysis
                </p>
                <h3 className="mt-1 text-2xl font-semibold">Gap Recommendations</h3>
                <p className="mt-2 text-sm text-text-muted">
                  Staples suggested from your current wardrobe and usage history.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setAnalyzeOpen(false)}
                className="rounded-lg border border-white/12 px-3 py-1.5 text-sm text-text-muted transition-colors hover:border-white/24"
              >
                Close
              </button>
            </div>

            {analyzeLoading && (
              <p className="text-sm text-text-muted">Analyzing your wardrobe…</p>
            )}
            {!analyzeLoading && analyzeError && (
              <p className="text-sm text-red-300">{analyzeError}</p>
            )}
            {!analyzeLoading && !analyzeError && analyzeResults.length === 0 && (
              <p className="text-sm text-text-muted">
                Your wardrobe already covers the basics.
              </p>
            )}
            {!analyzeLoading && !analyzeError && analyzeResults.length > 0 && (
              <div className="grid gap-3 md:grid-cols-2">
                {analyzeResults.map((rec) => (
                  <Card key={rec.templateId}>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent/60">
                      {rec.outfitPart}
                    </p>
                    <h4 className="mt-1 text-base font-semibold">{rec.name}</h4>
                    <p className="mt-2 text-sm text-text-muted">
                      {recommendationLine(rec)}
                    </p>
                  </Card>
                ))}
              </div>
            )}
          </GlassCard>
        </div>
      ) : null}
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────
function recommendationLine(rec) {
  const reason =
    Array.isArray(rec?.reasons) && rec.reasons.length ? rec.reasons[0] : "";
  if (rec?.summary) return rec.summary;
  if (reason === "LOW_DIVERSITY_SHOES")
    return "Improves shoe versatility for casual outfit rotation.";
  if (reason === "COLD_WEATHER_OUTERWEAR")
    return "Strengthens cold-weather layering coverage.";
  if (reason === "FORMAL_COVERAGE")
    return "Improves coverage for smarter and polished outfits.";
  return "Improves wardrobe coverage for more reliable outfit generation.";
}

// ── Data ──────────────────────────────────────────────────────────────────
const MICRO_TAGS = ["AI Labeling", "Weather-Aware", "Swap One Piece"];

const HOW_IT_WORKS_STEPS = [
  {
    icon: "upload",
    title: "Upload Items",
    description: "Add closet photos one by one or in bulk to begin your wardrobe catalog.",
  },
  {
    icon: "ai",
    title: "AI Labels Them",
    description: "Automatic labeling adds category, color, season, and formality metadata.",
  },
  {
    icon: "wardrobe",
    title: "Build Your Wardrobe",
    description: "Review your labeled pieces and maintain one organised inventory.",
  },
  {
    icon: "weather",
    title: "Generate by Weather & Occasion",
    description: "Recommendations adapt to conditions and how dressed up you want to be.",
  },
];

const FEATURES = [
  {
    icon: "vision",
    title: "AI Image Classification",
    description:
      "Recognises item attributes so your closet is searchable and generation-ready.",
    chips: ["OpenAI Vision"],
  },
  {
    icon: "meteo",
    title: "Weather-Aware Outfits",
    description: "Uses local weather to avoid suggestions that do not match the day.",
    chips: ["Open-Meteo"],
  },
  {
    icon: "rules",
    title: "Rule-Based Generation",
    description: "Combines deterministic rules with your labels for coherent outfits.",
    chips: ["Rule Engine"],
  },
  {
    icon: "swap",
    title: "Swap-One-Piece",
    description: "Change one item while preserving the rest of the generated look.",
  },
  {
    icon: "bulk",
    title: "Bulk Upload & Duplicate Detection",
    description: "Speed up onboarding and reduce repeated entries in your closet.",
  },
  {
    icon: "edit",
    title: "Edit Labels & Filter Dashboard",
    description: "Correct AI tags and filter by category, season, and formality.",
  },
];

const BENEFITS = [
  "Faster mornings",
  "Consistent, intentional style",
  "Fewer \"nothing to wear\" moments",
  "Better use of what you already own",
  "Weather-proof outfit choices",
];

const FAQS = [
  {
    question: "Where are images stored?",
    answer:
      "Images are associated with your Outfit Maker profile and used to build your wardrobe catalog.",
  },
  {
    question: "Can I edit labels?",
    answer:
      "Yes. You can manually adjust labels to keep item metadata accurate over time.",
  },
  {
    question: "How does weather work?",
    answer:
      "Outfit Maker reads weather conditions and applies temperature-aware outfit rules before generating recommendations.",
  },
  {
    question: "Can I manage multiple users or switch profiles?",
    answer:
      "Yes. Profiles stay separate so each user can manage an independent wardrobe and switch when needed.",
  },
  {
    question: "How does swap-one-piece work?",
    answer:
      "When an outfit is generated, you can replace a single item while keeping the rest of the look anchored.",
  },
];
