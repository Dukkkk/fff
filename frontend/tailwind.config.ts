import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f7f8fb",
          100: "#eef1f8",
          200: "#d7deef",
          300: "#b6c2e3",
          400: "#8598cf",
          500: "#5d73b9",
          600: "#46589a",
          700: "#38477d",
          800: "#2f3c67",
          900: "#293457"
        }
      },
      boxShadow: {
        soft: "0 12px 30px rgba(12, 18, 38, 0.10)",
        card: "0 10px 24px rgba(12, 18, 38, 0.08)"
      }
    }
  },
  plugins: []
} satisfies Config;

