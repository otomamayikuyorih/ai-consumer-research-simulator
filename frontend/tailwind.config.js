/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#b9dffd',
          300: '#7cc3fb',
          400: '#36a2f6',
          500: '#0c85e9',
          600: '#0267c7',
          700: '#0352a1',
          800: '#074685',
          900: '#0c3b6f',
          950: '#082549',
        }
      }
    },
  },
  plugins: [],
}
