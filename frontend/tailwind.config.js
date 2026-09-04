/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'tactile': {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#b9dffd',
          300: '#7cc5fb',
          400: '#36a9f7',
          500: '#0c8ee8',
          600: '#0070c6',
          700: '#0059a1',
          800: '#044c85',
          900: '#0a406e',
          950: '#062849',
        },
      },
    },
  },
  plugins: [],
}
