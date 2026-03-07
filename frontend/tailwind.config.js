/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // MERIDIAN design system — calming therapeutic palette
        meridian: {
          50: "#f0f7ff",
          100: "#e0efff",
          200: "#b9dbfe",
          300: "#7cbdfd",
          400: "#369afa",
          500: "#0c7deb",
          600: "#0062c9",
          700: "#014ea3",
          800: "#064386",
          900: "#0b396f",
          950: "#07244a",
        },
        warmth: {
          50: "#fdf8f0",
          100: "#faebd7",
          200: "#f5d5ae",
          300: "#eeb87b",
          400: "#e69548",
          500: "#df7a26",
          600: "#d0621c",
          700: "#ac4b19",
          800: "#8a3c1c",
          900: "#70331a",
        },
        surface: {
          primary: "#fafbfd",
          secondary: "#f4f6fa",
          tertiary: "#ebeef5",
          card: "#ffffff",
        },
        ink: {
          primary: "#1a2332",
          secondary: "#4a5568",
          muted: "#8794a7",
          light: "#b8c4d4",
        },
      },
      fontFamily: {
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [],
};
