/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "#0f131c",
        surface: "#121720",
        panel: "#131a24",
        border: "#202634",
        text: {
          DEFAULT: "#e8eaed",
          muted: "#aab1bf",
        },
        accent: "#4ade80", // subtle green accent
      },
      borderRadius: {
        xl: "14px",
        "2xl": "20px",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(0,0,0,0.25)",
      },
      keyframes: {
        breathe: {
          "0%, 100%": { transform: "translateY(0) scale(1)" },
          "50%": { transform: "translateY(-1px) scale(1.01)" },
        },
      },
      animation: {
        breathe: "breathe 3s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
