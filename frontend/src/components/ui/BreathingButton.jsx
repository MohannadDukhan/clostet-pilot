export default function BreathingButton({ children, className = "", ...props }) {
  return (
    <button
      {...props}
      className={`btn btn-accent breathe ${className}`}
    >
      {children}
    </button>
  );
}