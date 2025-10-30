import Container from "../components/Container";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <Container className="text-center">
      <h2 className="text-2xl font-semibold">Page not found</h2>
      <p className="text-text-muted my-3">The page you requested does not exist.</p>
      <Link to="/" className="btn">Go Home</Link>
    </Container>
  );
}