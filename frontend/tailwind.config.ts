import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0B0F14",
          900: "#10151C",
          800: "#161D27",
          700: "#212A37",
          600: "#2E3A4A",
        },
        paper: {
          50: "#F7F8FA",
          100: "#EEF1F5",
          200: "#DDE3EA",
        },
        signal: {
          DEFAULT: "#3E8FF2",
          soft: "#8FBCFA",
          deep: "#1C5FC7",
        },
        amber: {
          DEFAULT: "#F2A93E",
        },
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        sans: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 24px -12px rgba(0,0,0,0.5)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
    },
  },
  plugins: [],
} satisfies Config;
