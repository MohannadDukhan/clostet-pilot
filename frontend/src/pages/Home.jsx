import { Link } from "react-router-dom";
import Container from "../components/Container";

export default function Home() {
  return (
    <Container>
      <section className="grid md:grid-cols-2 gap-8 items-center">
        <div className="space-y-6">
          <h1 className="text-4xl md:text-5xl font-semibold leading-tight tracking-tight">
            Closet Pilot
          </h1>
          <p className="text-text-muted max-w-prose">
            AI‑assisted outfit planning, made simple. Upload your clothes, let the model classify them, and build your perfect fits.
          </p>
          <div className="flex gap-3">
            <Link to="/create-user" className="btn btn-accent breathe">Get Started →</Link>
            <Link to="/about" className="btn">Learn More</Link>
          </div>
        </div>
        <div className="relative">
          <div className="card p-6">
            <div className="aspect-[4/3] rounded-2xl bg-[radial-gradient(circle_at_30%_20%,rgba(74,222,128,0.08),transparent_45%),radial-gradient(circle_at_70%_60%,rgba(74,222,128,0.06),transparent_35%)] border border-border grid place-items-center">
              <div className="text-center text-sm text-text-muted">
                <div className="text-base mb-1">Glassmorphism preview</div>
                <div className="opacity-80">Your wardrobe will live here</div>
              </div>
            </div>
          </div>
        </div>
      </section>

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
  { title: "Upload your clothes", desc: "Drag and drop images or add items with details." },
  { title: "AI classifies them", desc: "Colors, category, season, formality detected on upload." },
  { title: "Build outfits", desc: "Start mixing items. Outfit generator is coming soon." },
];