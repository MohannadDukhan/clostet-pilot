import { Link } from "react-router-dom";
import Container from "../components/Container";

export default function About() {
  return (
    <Container className="py-10 space-y-10">
      {/* Hero */}
      <section className="grid gap-8 md:grid-cols-[2fr,1.2fr] items-start">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-text-muted">
            About Closet Pilot
          </p>
          <h1 className="mt-2 text-3xl md:text-4xl font-semibold bg-gradient-to-r from-emerald-300 via-emerald-200 to-sky-300 bg-clip-text text-transparent">
            A cleaner, smarter wardrobe.
          </h1>
          <p className="mt-3 text-sm md:text-base text-text-muted">
            Closet Pilot turns the clothes you already own into a digital
            wardrobe and suggests outfits around real weather and simple
            style rules. It is designed to be practical first: fast uploads,
            clear labels, and suggestions that respect season, formality, and
            what you actually like to wear.
          </p>


          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/create-user" className="btn btn-accent breathe">
              Create a profile
            </Link>
            <Link to="/upload" className="btn">
              Upload items
            </Link>
            <Link to="/generate" className="btn">
              Generate an outfit
            </Link>
          </div>
        </div>

        {/* Side panel / quick facts */}
        <aside className="card p-5 bg-gradient-to-b from-emerald-500/10 via-emerald-500/5 to-sky-500/5 border-emerald-500/30">
          <h2 className="text-sm font-semibold mb-3 text-text">
            What Closet Pilot focuses on
          </h2>
          <ul className="space-y-2 text-xs text-text-muted">
            <li>• Fast uploads with automatic classification.</li>
            <li>• Weather-aware suggestions using your city and date.</li>
            <li>• Simple controls to include, exclude, or lock pieces.</li>
            <li>• A dashboard that keeps your wardrobe organised.</li>
          </ul>

          <div className="mt-4 border-t border-border/60 pt-4 text-[11px]">
            <p className="font-medium mb-1 text-text">
              Tech stack at a glance
            </p>
            <p className="text-text-muted">
              FastAPI · SQLModel · SQLite · React · Vite · Tailwind · OpenAI
              Vision · Open-Meteo
            </p>
          </div>
        </aside>
      </section>

      {/* How it works */}
      <section className="grid gap-6 md:grid-cols-3">
        <div className="card p-5 bg-panel/80">
          <h3 className="text-sm font-semibold mb-2">1. Digitise</h3>
          <p className="text-xs text-text-muted">
            Upload photos of your clothes. The system classifies each piece by
            part, category, color, season, and formality. You can adjust any
            label directly from the wardrobe dashboard.
          </p>
        </div>
        <div className="card p-5 bg-panel/80">
          <h3 className="text-sm font-semibold mb-2">2. Understand context</h3>
          <p className="text-xs text-text-muted">
            Closet Pilot pulls real weather for your city and infers a season
            bucket. This keeps suggestions grounded in what actually makes sense
            to wear that day.
          </p>
        </div>
        <div className="card p-5 bg-panel/80">
          <h3 className="text-sm font-semibold mb-2">3. Generate outfits</h3>
          <p className="text-xs text-text-muted">
            Choose the occasion, lock pieces you want to keep, exclude anything
            that is off-limits, and let the generator build a complete look.
            You can now also swap individual pieces without losing the rest of
            the outfit.
          </p>
        </div>
      </section>

      {/* Footer note */}
      <section className="card p-5 text-[11px] text-text-muted">
        <p>
          Closet Pilot was built as a Software Engineering capstone project at
          Carleton University. The current version runs on a local SQLite
          database and local file storage, with a clear path to future work such
          as cloud storage, multi-device sync, richer personalization, and
          automatic extraction of multiple items from a single full-body photo.
        </p>
      </section>
    </Container>
  );
}
