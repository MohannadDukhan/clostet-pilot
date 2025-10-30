import Container from "../components/Container";

export default function About() {
  return (
    <Container className="space-y-4">
      <h2 className="text-2xl font-semibold">About</h2>
      <p className="text-text-muted max-w-prose">
        Closet Pilot uses a FastAPI backend with SQLite to store your wardrobe and integrates with GPT‑4o‑mini to auto‑classify items on upload.
        This frontend is built with React + Vite, Tailwind v4, and Framer Motion.
      </p>
      <ul className="list-disc pl-6 text-sm text-text-muted space-y-1">
        <li>Local accounts today, auth flow coming soon</li>
        <li>Upload, view, and reclassify items</li>
        <li>Outfit generator placeholder for the next iteration</li>
      </ul>
    </Container>
  );
}