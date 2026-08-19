/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef6ff",
          100: "#d9ebff",
          200: "#bcddff",
          300: "#8ec8ff",
          400: "#59aaff",
          500: "#3388ff",
          600: "#1a66f5",
          700: "#1350e1",
          800: "#1542b6",
          900: "#173b8f",
          950: "#13264f",
        },
      },
    },
  },
  plugins: [],
};