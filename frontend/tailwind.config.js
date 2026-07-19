/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0f17",
        panel: "#131926",
        edge: "#1f2937",
        accent: "#6366f1",
      },
    },
  },
  plugins: [],
};
