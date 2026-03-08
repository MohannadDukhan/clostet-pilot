import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Container from "../components/Container";
import { API } from "../api";

function GlassCard({ className = "", hover = true, children }) {
  const hoverClass = hover
    ? "transition-all duration-300 hover:-translate-y-1 hover:border-accent/45 hover:shadow-[0_18px_50px_rgba(0,0,0,0.35),0_0_30px_rgba(74,222,128,0.14)]"
    : "";

  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border border-white/16 bg-white/[0.08] backdrop-blur-xl ${hoverClass} ${className}`}
    >
      <div className="pointer-events-none absolute -right-16 -top-16 h-36 w-36 rounded-full bg-gradient-to-br from-accent/18 to-transparent blur-2xl opacity-70 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="pointer-events-none absolute inset-0 rounded-2xl [background:linear-gradient(130deg,rgba(255,255,255,0.10),transparent_36%,transparent_64%,rgba(255,255,255,0.06))] opacity-55" />
      <div className="relative">{children}</div>
    </div>
  );
}

function SectionHeading({ eyebrow, title, subtitle }) {
  return (
    <div className="max-w-3xl space-y-3">
      <p className="text-xs uppercase tracking-[0.24em] text-accent/90">{eyebrow}</p>
      <h2 className="text-2xl font-semibold tracking-tight md:text-4xl">{title}</h2>
      {subtitle ? <p className="text-text-muted">{subtitle}</p> : null}
    </div>
  );
}

function SectionDivider() {
  return <div className="h-px w-full bg-gradient-to-r from-transparent via-accent/40 to-transparent" />;
}

function Icon({ name, className = "h-5 w-5" }) {
  const base = `stroke-current fill-none ${className}`;

  if (name === "upload") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M12 16V4" />
        <path d="M8 8l4-4 4 4" />
        <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
      </svg>
    );
  }

  if (name === "ai") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <rect x="5" y="5" width="14" height="14" rx="3" />
        <path d="M9 9h6v6H9z" />
        <path d="M3 10h2M3 14h2M19 10h2M19 14h2M10 3v2M14 3v2M10 19v2M14 19v2" />
      </svg>
    );
  }

  if (name === "wardrobe") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12H4z" />
        <path d="M12 4v14" />
        <path d="M9 10h.01M15 10h.01" />
      </svg>
    );
  }

  if (name === "weather") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M6 15a4 4 0 0 1 2.6-7A5 5 0 0 1 18 10a3 3 0 1 1 0 6H6z" />
        <path d="M8 19l-1 2M12 19l-1 2M16 19l-1 2" />
      </svg>
    );
  }

  if (name === "vision") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <rect x="3" y="4" width="18" height="14" rx="2" />
        <path d="M8 14l3-3 3 2 3-4" />
        <circle cx="9" cy="9" r="1" />
      </svg>
    );
  }

  if (name === "meteo") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M12 3v3M5.6 5.6l2.1 2.1M3 12h3M5.6 18.4l2.1-2.1M12 18a6 6 0 1 0 0-12" />
      </svg>
    );
  }

  if (name === "rules") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M8 6h11M8 12h11M8 18h11" />
        <path d="M3 6h.01M3 12h.01M3 18h.01" />
      </svg>
    );
  }

  if (name === "swap") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M7 7h10l-3-3" />
        <path d="M17 17H7l3 3" />
      </svg>
    );
  }

  if (name === "bulk") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <rect x="3" y="7" width="8" height="8" rx="1" />
        <rect x="13" y="7" width="8" height="8" rx="1" />
        <path d="M7 15v3h10v-3" />
      </svg>
    );
  }

  if (name === "edit") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M4 20h4l10-10-4-4L4 16v4z" />
        <path d="M12 6l4 4" />
      </svg>
    );
  }

  if (name === "storage") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <ellipse cx="12" cy="6" rx="7" ry="3" />
        <path d="M5 6v8c0 1.7 3.1 3 7 3s7-1.3 7-3V6" />
      </svg>
    );
  }

  if (name === "labels") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M4 11V5h6l9 9-6 6-9-9z" />
        <circle cx="8.5" cy="8.5" r="1" />
      </svg>
    );
  }

  if (name === "users") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <circle cx="9" cy="8" r="3" />
        <path d="M3 19c0-2.8 2.7-5 6-5s6 2.2 6 5" />
        <path d="M17 7c1.9 0 3.5 1.6 3.5 3.5S18.9 14 17 14" />
      </svg>
    );
  }

  if (name === "arrow") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="1.8" aria-hidden="true">
        <path d="M5 12h14" />
        <path d="M15 7l5 5-5 5" />
      </svg>
    );
  }

  if (name === "check") {
    return (
      <svg viewBox="0 0 24 24" className={base} strokeWidth="2" aria-hidden="true">
        <path d="M6 12l4 4 8-8" />
      </svg>
    );
  }

  return null;
}

function CardIcon({ name }) {
  return (
    <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg border border-accent/35 bg-accent/15 text-accent">
      <Icon name={name} className="h-5 w-5" />
    </div>
  );
}

export default function Home() {
  const navigate = useNavigate();
  const [openFaqIndex, setOpenFaqIndex] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [analyzeOpen, setAnalyzeOpen] = useState(false);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [analyzeError, setAnalyzeError] = useState("");
  const [analyzeResults, setAnalyzeResults] = useState([]);

  useEffect(() => {
    const syncSelectedUser = () => {
      try {
        const raw = localStorage.getItem("cp:user");
        const parsed = raw ? JSON.parse(raw) : null;
        setSelectedUserId(parsed?.id ? Number(parsed.id) : null);
      } catch {
        setSelectedUserId(null);
      }
    };

    syncSelectedUser();
    window.addEventListener("storage", syncSelectedUser);
    window.addEventListener("focus", syncSelectedUser);
    return () => {
      window.removeEventListener("storage", syncSelectedUser);
      window.removeEventListener("focus", syncSelectedUser);
    };
  }, []);

  const goToHowItWorks = () => {
    const section = document.getElementById("how-it-works");
    section?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleGetStarted = () => {
    let hasSelectedUser = false;

    try {
      const raw = localStorage.getItem("cp:user");
      const parsed = raw ? JSON.parse(raw) : null;
      hasSelectedUser = Boolean(parsed?.id);
    } catch {
      hasSelectedUser = false;
    }

    navigate(hasSelectedUser ? "/dashboard" : "/create-user");
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
      <div className="pointer-events-none absolute inset-0">
        <div className="homefx-orb absolute -left-40 -top-36 h-[34rem] w-[34rem] rounded-full bg-[radial-gradient(circle,rgba(74,222,128,0.22)_0%,rgba(74,222,128,0.08)_35%,transparent_72%)] blur-3xl" />
        <div className="homefx-orb absolute -right-32 -top-28 h-[30rem] w-[30rem] rounded-full bg-[radial-gradient(circle,rgba(56,189,248,0.16)_0%,rgba(56,189,248,0.06)_36%,transparent_74%)] blur-3xl" />
        <div className="absolute inset-0 opacity-[0.085] [background-image:linear-gradient(rgba(255,255,255,0.16)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.12)_1px,transparent_1px)] [background-size:42px_42px]" />
        <div className="absolute inset-0 opacity-[0.04] [background-image:repeating-radial-gradient(circle_at_0_0,rgba(255,255,255,0.6)_0,rgba(255,255,255,0.6)_1px,transparent_1px,transparent_3px)]" />
      </div>

      <Container className="relative z-10 space-y-10 pb-8 md:space-y-12">
        <section className="grid gap-10 pb-3 pt-10 md:pb-6 md:pt-14 lg:grid-cols-2 lg:gap-14">
          <div className="space-y-6">
            <p className="inline-flex items-center gap-2 rounded-full border border-accent/35 bg-accent/10 px-4 py-1.5 text-xs text-accent">
              <span className="homefx-glow h-2 w-2 rounded-full bg-accent" />
              Smart outfit planning from your real wardrobe
            </p>

            <h1 className="text-5xl font-semibold leading-[0.92] tracking-tight md:text-7xl lg:text-8xl">
              <span className="bg-gradient-to-r from-white via-green-200 to-cyan-200 bg-clip-text text-transparent drop-shadow-[0_0_16px_rgba(74,222,128,0.2)]">
                Closet Pilot
              </span>
            </h1>

            <p className="max-w-xl text-base text-text-muted md:text-lg">
              Wardrobe digitization, AI outfit generation, and weather awareness in one
              premium workflow.
            </p>

            <div className="flex flex-col gap-3 pt-1 sm:flex-row">
              <button
                type="button"
                onClick={handleGetStarted}
                className="group relative inline-flex items-center justify-center overflow-hidden rounded-2xl border border-accent/50 bg-accent px-5 py-2.5 font-medium text-bg shadow-[0_0_30px_rgba(74,222,128,0.35)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_0_40px_rgba(74,222,128,0.45)]"
              >
                <span className="pointer-events-none absolute inset-0 homefx-button-shimmer bg-gradient-to-r from-transparent via-white/25 to-transparent" />
                <span className="relative">Get Started</span>
              </button>
              <button
                type="button"
                onClick={goToHowItWorks}
                className="inline-flex items-center justify-center rounded-2xl border border-white/26 bg-white/[0.06] px-5 py-2.5 font-medium text-text transition-all duration-300 hover:-translate-y-0.5 hover:border-accent/40 hover:bg-white/[0.12]"
              >
                See How It Works
              </button>
            </div>

            <div className="flex flex-wrap gap-2 pt-1">
              {MICRO_TAGS.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-white/22 bg-white/[0.06] px-3 py-1 text-xs text-text-muted"
                >
                  {tag}
                </span>
              ))}
            </div>

            {selectedUserId ? (
              <button
                type="button"
                onClick={handleAnalyzeWardrobe}
                className="inline-flex items-center justify-center rounded-2xl border border-accent/45 bg-accent/12 px-5 py-2.5 text-sm font-medium text-accent transition-all duration-300 hover:-translate-y-0.5 hover:bg-accent/20"
              >
                Analyze My Wardrobe
              </button>
            ) : null}
          </div>

          <GlassCard className="relative bg-gradient-to-br from-white/14 via-white/8 to-transparent p-5 md:p-7">
            <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-2xl">
              <div className="homefx-scan absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-accent/25 via-accent/5 to-transparent opacity-25" />
            </div>

            <div className="mb-5 flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-text-muted">MOCK PREVIEW</p>
                <h3 className="mt-1 text-lg font-medium">Generated Outfit</h3>
              </div>
              <span className="rounded-full border border-accent/40 bg-accent/15 px-3 py-1 text-xs text-accent">
                4\u00B0C Cold
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {MOCK_OUTFIT.map((piece) => (
                <GlassCard key={piece.slot} className="bg-white/8 p-4">
                  <p className="mb-2 text-xs uppercase tracking-[0.16em] text-text-muted">
                    {piece.slot}
                  </p>
                  <p className="font-medium">{piece.item}</p>
                </GlassCard>
              ))}
            </div>

            <p className="mt-4 text-xs text-text-muted">
              Outfit assembled directly from your wardrobe inventory.
            </p>
          </GlassCard>
        </section>

        <SectionDivider />

        <section id="how-it-works" className="rounded-3xl border border-white/10 bg-white/[0.03] px-5 py-12 md:px-10 md:py-16">
          <div className="space-y-8">
            <SectionHeading
              eyebrow="How It Works"
              title="From Closet Photos To Complete Outfits"
              subtitle="A clear workflow that turns your closet into practical recommendations."
            />

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {HOW_IT_WORKS_STEPS.map((step, index) => (
                <GlassCard key={step.title} className="p-5">
                  <CardIcon name={step.icon} />
                  <p className="mb-2 text-xs uppercase tracking-[0.2em] text-accent/90">Step {index + 1}</p>
                  <h3 className="mb-2 text-lg font-semibold">{step.title}</h3>
                  <p className="text-sm text-text-muted">{step.description}</p>
                </GlassCard>
              ))}
            </div>
          </div>
        </section>

        <SectionDivider />

        <section className="rounded-3xl border border-white/10 bg-white/[0.03] px-5 py-12 md:px-10 md:py-16">
          <div className="space-y-8">
            <SectionHeading
              eyebrow="Feature Highlights"
              title="Core Engine, Premium Experience"
              subtitle="Technical foundations designed for speed, clarity, and reliable outfit output."
            />

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map((feature) => (
                <GlassCard key={feature.title} className="p-5">
                  <CardIcon name={feature.icon} />
                  <h3 className="mb-2 text-lg font-semibold">{feature.title}</h3>
                  <p className="text-sm text-text-muted">{feature.description}</p>
                  {feature.chips?.length ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {feature.chips.map((chip) => (
                        <span
                          key={chip}
                          className="rounded-full border border-accent/30 bg-accent/12 px-2.5 py-1 text-[11px] text-accent"
                        >
                          {chip}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </GlassCard>
              ))}
            </div>
          </div>
        </section>

        <SectionDivider />

        <section className="rounded-3xl border border-white/10 bg-white/[0.03] px-5 py-12 md:px-10 md:py-16">
          <div className="grid gap-6 lg:grid-cols-2">
            <GlassCard className="p-6 md:p-8">
              <SectionHeading
                eyebrow="What You Get"
                title="Better Outfit Decisions, Less Daily Friction"
                subtitle="Many mornings are lost to mismatched options and weather misses. Closet Pilot keeps your wardrobe visible and delivers combinations that fit your context."
              />
            </GlassCard>

            <GlassCard className="p-6 md:p-8">
              <h3 className="mb-4 text-xl font-semibold">Benefits</h3>
              <ul className="space-y-3">
                {BENEFITS.map((benefit) => (
                  <li key={benefit} className="flex items-center gap-3 text-text-muted">
                    <span className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-accent/40 bg-accent/14 text-accent">
                      <Icon name="check" className="h-4 w-4" />
                    </span>
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>
            </GlassCard>
          </div>
        </section>

        <SectionDivider />

        <section className="rounded-3xl border border-white/10 bg-white/[0.03] px-5 py-12 md:px-10 md:py-16">
          <div className="space-y-8">
            <SectionHeading
              eyebrow="Demo Flow"
              title="Static Outfit Pipeline"
              subtitle="A futuristic preview of how upload, weather context, and generation connect."
            />

            <div className="grid gap-4 lg:grid-cols-[1fr_auto_1fr_auto_1fr] lg:items-center">
              <GlassCard className="p-5">
                <div className="mb-3 inline-flex h-7 w-7 items-center justify-center rounded-full border border-accent/40 bg-accent/15 text-xs text-accent">
                  1
                </div>
                <p className="mb-2 text-sm font-medium text-accent">Upload Photo</p>
                <p className="mb-3 text-sm text-text-muted">Item is analyzed and converted to structured labels.</p>
                <div className="rounded-xl border border-white/16 bg-black/25 p-3 font-mono text-xs text-green-200">
                  classified_as: top / hoodie / navy / fall / casual
                </div>
              </GlassCard>

              <div className="hidden justify-center text-accent/80 lg:flex">
                <Icon name="arrow" className="h-6 w-6 drop-shadow-[0_0_10px_rgba(74,222,128,0.45)]" />
              </div>

              <GlassCard className="p-5">
                <div className="mb-3 inline-flex h-7 w-7 items-center justify-center rounded-full border border-accent/40 bg-accent/15 text-xs text-accent">
                  2
                </div>
                <p className="mb-2 text-sm font-medium text-accent">Weather Context</p>
                <p className="mb-3 text-sm text-text-muted">Conditions shape layering and warmth constraints.</p>
                <div className="rounded-xl border border-white/16 bg-black/25 p-3 font-mono text-xs text-cyan-200">
                  weather: 4\u00B0C | profile: cold
                </div>
              </GlassCard>

              <div className="hidden justify-center text-accent/80 lg:flex">
                <Icon name="arrow" className="h-6 w-6 drop-shadow-[0_0_10px_rgba(74,222,128,0.45)]" />
              </div>

              <GlassCard className="p-5">
                <div className="mb-3 inline-flex h-7 w-7 items-center justify-center rounded-full border border-accent/40 bg-accent/15 text-xs text-accent">
                  3
                </div>
                <p className="mb-2 text-sm font-medium text-accent">Outfit Output</p>
                <p className="mb-3 text-sm text-text-muted">Generated cards appear and can be refined.</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg border border-white/20 bg-white/6 p-2">Top: Navy Hoodie</div>
                  <div className="rounded-lg border border-white/20 bg-white/6 p-2">Bottom: Black Jeans</div>
                  <div className="rounded-lg border border-white/20 bg-white/6 p-2">Outerwear: Wool Coat</div>
                  <div className="rounded-lg border border-white/20 bg-white/6 p-2">Shoes: Leather Boots</div>
                </div>
              </GlassCard>
            </div>

            <p className="text-sm text-text-muted">
              If one piece is off, use swap-one-piece and keep the rest of the outfit anchored.
            </p>
          </div>
        </section>

        <SectionDivider />

        <section className="rounded-3xl border border-white/10 bg-white/[0.03] px-5 py-12 md:px-10 md:py-16">
          <div className="space-y-8">
            <SectionHeading
              eyebrow="FAQ"
              title="Common Questions"
              subtitle="Quick answers about storage, controls, and generation behavior."
            />

            <div className="space-y-3">
              {FAQS.map((faq, index) => {
                const isOpen = openFaqIndex === index;

                return (
                  <GlassCard key={faq.question} className="overflow-hidden" hover={false}>
                    <button
                      type="button"
                      className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                      onClick={() => setOpenFaqIndex(isOpen ? null : index)}
                    >
                      <span className="font-medium">{faq.question}</span>
                      <span className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-accent/35 bg-accent/12 text-lg leading-none text-accent">
                        {isOpen ? "-" : "+"}
                      </span>
                    </button>

                    <div
                      className={`grid transition-all duration-300 ease-out ${
                        isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                      }`}
                    >
                      <div className="overflow-hidden px-5 pb-5 text-sm text-text-muted">
                        {faq.answer}
                      </div>
                    </div>
                  </GlassCard>
                );
              })}
            </div>
          </div>
        </section>

        <section className="pb-8 pt-2">
          <GlassCard
            hover={false}
            className="rounded-3xl border-accent/30 bg-gradient-to-r from-accent/24 via-white/8 to-transparent p-8 md:p-12"
          >
            <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-3xl font-semibold tracking-tight">Ready to digitize your closet?</h3>
                <p className="mt-2 text-sm text-text-muted">Closet Pilot Capstone Project.</p>
              </div>
              <button
                type="button"
                onClick={() => navigate("/upload")}
                className="inline-flex items-center justify-center rounded-2xl border border-accent/55 bg-accent px-6 py-3 font-medium text-bg shadow-[0_0_34px_rgba(74,222,128,0.38)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_0_46px_rgba(74,222,128,0.5)]"
              >
                Upload Your First Item
              </button>
            </div>
          </GlassCard>
        </section>
      </Container>

      {analyzeOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/65 px-4 py-6 backdrop-blur-sm">
          <GlassCard hover={false} className="max-h-[88vh] w-full max-w-3xl overflow-y-auto p-6 md:p-8">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-accent/90">Wardrobe Analysis</p>
                <h3 className="mt-1 text-2xl font-semibold">Gap Recommendations</h3>
                <p className="mt-2 text-sm text-text-muted">
                  Deterministic staples suggested from your current wardrobe and usage history.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setAnalyzeOpen(false)}
                className="rounded-xl border border-white/20 bg-white/[0.06] px-3 py-1.5 text-sm text-text-muted hover:bg-white/[0.12]"
              >
                Close
              </button>
            </div>

            {analyzeLoading ? (
              <GlassCard hover={false} className="p-6 text-sm text-text-muted">
                Analyzing your wardrobe...
              </GlassCard>
            ) : null}

            {!analyzeLoading && analyzeError ? (
              <GlassCard hover={false} className="p-6 text-sm text-red-200">
                {analyzeError}
              </GlassCard>
            ) : null}

            {!analyzeLoading && !analyzeError && analyzeResults.length === 0 ? (
              <GlassCard hover={false} className="p-6 text-sm text-text-muted">
                Your wardrobe already covers the basics.
              </GlassCard>
            ) : null}

            {!analyzeLoading && !analyzeError && analyzeResults.length > 0 ? (
              <div className="grid gap-3 md:grid-cols-2">
                {analyzeResults.map((rec) => (
                  <GlassCard key={rec.templateId} className="p-5">
                    <p className="text-xs uppercase tracking-[0.2em] text-accent/80">{rec.outfitPart}</p>
                    <h4 className="mt-1 text-lg font-semibold">{rec.name}</h4>
                    <p className="mt-2 text-sm text-text-muted">{recommendationLine(rec)}</p>
                  </GlassCard>
                ))}
              </div>
            ) : null}
          </GlassCard>
        </div>
      ) : null}

      <style>{`
        @keyframes homefxScan {
          0% { transform: translateY(-140%); }
          100% { transform: translateY(280%); }
        }

        @keyframes homefxOrb {
          0%, 100% { transform: scale(1) translateY(0); }
          50% { transform: scale(1.07) translateY(10px); }
        }

        @keyframes homefxPulse {
          0%, 100% { opacity: 0.8; }
          50% { opacity: 1; }
        }

        @keyframes homefxButtonShimmer {
          0% { transform: translateX(-140%); }
          100% { transform: translateX(140%); }
        }

        .homefx-scan {
          animation: homefxScan 5.5s linear infinite;
        }

        .homefx-orb {
          animation: homefxOrb 14s ease-in-out infinite;
        }

        .homefx-glow {
          animation: homefxPulse 2.8s ease-in-out infinite;
        }

        .homefx-button-shimmer {
          animation: homefxButtonShimmer 2.8s linear infinite;
        }
      `}</style>
    </div>
  );
}

function recommendationLine(rec) {
  const reason = Array.isArray(rec?.reasons) && rec.reasons.length ? rec.reasons[0] : "";
  if (rec?.summary) return rec.summary;
  if (reason === "LOW_DIVERSITY_SHOES") return "Improves shoe versatility for casual outfit rotation.";
  if (reason === "COLD_WEATHER_OUTERWEAR") return "Strengthens cold-weather layering coverage.";
  if (reason === "FORMAL_COVERAGE") return "Improves coverage for smarter and formal outfits.";
  return "Improves wardrobe coverage for more reliable outfit generation.";
}

const MICRO_TAGS = ["AI Labeling", "Weather-Aware", "Swap One Piece"];

const MOCK_OUTFIT = [
  { slot: "Top", item: "Navy Hoodie" },
  { slot: "Bottom", item: "Black Jeans" },
  { slot: "Outerwear", item: "Wool Coat" },
  { slot: "Shoes", item: "Leather Boots" },
];

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
    description: "Review your labeled pieces and maintain one organized inventory.",
  },
  {
    icon: "weather",
    title: "Generate Outfits By Weather + Formality",
    description: "Recommendations adapt to conditions and how dressed up you want to be.",
  },
];

const FEATURES = [
  {
    icon: "vision",
    title: "AI Image Classification",
    description: "Recognizes item attributes so your closet is searchable and generation-ready.",
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
    title: "Bulk Upload + Duplicate Detection",
    description: "Speed up onboarding and reduce repeated entries in your closet.",
  },
  {
    icon: "edit",
    title: "Edit Labels + Filtering Dashboard",
    description: "Correct AI tags and filter by category, season, and formality.",
  },
];

const BENEFITS = [
  "Faster mornings",
  "Consistent style",
  "Fewer \"nothing to wear\" moments",
  "Better use of what you own",
];

const FAQS = [
  {
    question: "Where are images stored?",
    answer: "Images are associated with your Closet Pilot profile and used to build your wardrobe catalog.",
  },
  {
    question: "Can I edit labels?",
    answer: "Yes. You can manually adjust labels to keep item metadata accurate over time.",
  },
  {
    question: "How does weather work?",
    answer: "Closet Pilot reads weather conditions and applies temperature-aware outfit rules before generating recommendations.",
  },
  {
    question: "Can I manage multiple users or switch profiles?",
    answer: "Yes. Profiles stay separate so each user can manage an independent wardrobe and switch when needed.",
  },
  {
    question: "How does swap-one-piece work?",
    answer: "When an outfit is generated, you can replace a single item while keeping the rest of the look anchored.",
  },
];
