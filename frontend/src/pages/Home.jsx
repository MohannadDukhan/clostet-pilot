import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Container from "../components/Container";
import { listUserItems, imageSrc } from "../api";

export default function Home() {
  const [user, setUser] = useState(null);
  const [previewItems, setPreviewItems] = useState([]);
  const [loadingPreview, setLoadingPreview] = useState(false);

  useEffect(() => {
    // read selected user from localStorage (Navbar sets "cp:user")
    try {
      const raw = localStorage.getItem("cp:user");
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (!parsed?.id) return;

      setUser(parsed);

      (async () => {
        setLoadingPreview(true);
        try {
          const items = await listUserItems(parsed.id);
          setPreviewItems((items || []).slice(0, 9)); // show up to 9 items
        } catch {
          // non critical on home page
        } finally {
          setLoadingPreview(false);
        }
      })();
    } catch {
      // ignore parse errors
    }
  }, []);

  return (
    <Container>
      <section className="grid md:grid-cols-2 gap-8 items-center">
        {/* left side hero text */}
        <div className="space-y-6">
          <h1 className="text-4xl md:text-5xl font-semibold leading-tight tracking-tight">
            Closet Pilot
          </h1>
          <p className="text-text-muted max-w-prose">
            AI-assisted outfit planning, made simple. upload your clothes,
            let the model classify them, and build your perfect fits.
          </p>
          <div className="flex gap-3">
            <Link to="/create-user" className="btn btn-accent breathe">
              Get Started →
            </Link>
            <Link to="/about" className="btn">
              Learn More
            </Link>
          </div>
        </div>

        {/* right side preview */}
        <div className="relative">
          <div className="card p-6">
            <div className="relative flex items-center justify-center h-full">
              {/* colored glow behind the pill */}
              <div className="pointer-events-none absolute inset-0 blur-3xl opacity-60 bg-[radial-gradient(circle_at_0%_0%,rgba(74,222,128,0.18),transparent_55%),radial-gradient(circle_at_100%_100%,rgba(59,130,246,0.18),transparent_50%),radial-gradient(circle_at_50%_100%,rgba(244,114,182,0.16),transparent_55%)]" />

              {/* clickable wardrobe pill */}
              <Link
                to="/dashboard"
                className="group relative max-w-xs w-full rounded-[2rem] bg-surface/80 border border-border/70 shadow-xl p-3 overflow-hidden transform transition-transform duration-300 ease-out hover:scale-[1.05] hover:shadow-2xl"
              >
                {/* base content (grid / placeholder / loading) */}
                {loadingPreview ? (
                  <div className="flex items-center justify-center h-32 text-xs text-text-muted animate-pulse">
                    loading your wardrobe preview…
                  </div>
                ) : user && previewItems.length > 0 ? (
                  <div className="grid grid-cols-3 gap-2">
                    {previewItems.map((it) => (
                      <div
                        key={it.id}
                        className="rounded-xl overflow-hidden bg-bg border border-border/40 aspect-[3/4]"
                      >
                        <img
                          src={imageSrc(it)}
                          alt={it.category || "wardrobe item"}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-32 text-center text-xs text-text-muted px-4">
                    <div className="text-sm mb-1 font-medium">
                      glassmorphism preview
                    </div>
                    <div className="opacity-80">
                      select a user and upload a few items to see your wardrobe
                      grid.
                    </div>
                  </div>
                )}

                {/* overlay text */}
                <div
                  className="
                    pointer-events-none absolute inset-0 flex flex-col items-center justify-center
                    bg-black/12 backdrop-blur-[1px]
                    group-hover:bg-black/6 group-hover:backdrop-blur-[0.5px]
                    transition-all duration-300
                  "
                >
                  <div className="text-sm uppercase tracking-[0.18em] text-accent/80 mb-1">
                    {user?.name ? `${user.name}'s` : "your"}
                  </div>

                  <div
                    className="
                      text-2xl font-semibold
                      bg-gradient-to-r from-green-300 via-emerald-200 to-sky-300
                      bg-clip-text text-transparent
                    "
                  >
                    wardrobe
                  </div>

                  <div className="mt-2 text-xs text-text-muted/85">
                    click to view all items
                  </div>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* feature pills */}
      <section className="grid sm:grid-cols-3 gap-4 mt-12">
        {FEATURES.map((f) => (
          <div key={f.title} className="card p-5">
            <div className="text-sm font-medium mb-1">{f.title}</div>
            <p className="text-xs text-text-muted">{f.desc}</p>
          </div>
        ))}
      </section>
    </Container>
  );
}

const FEATURES = [
  {
    title: "Upload your clothes",
    desc: "drag and drop images or add items with details.",
  },
  {
    title: "AI classifies them",
    desc: "colors, category, season, formality detected on upload.",
  },
  {
    title: "Build outfits",
    desc: "generate weather aware outfits from your own wardrobe.",
  },
];
