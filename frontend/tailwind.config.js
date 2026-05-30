/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        ink: '#111827',
        surface: '#f3f5f8',
        graphite: '#1f2937',
        console: '#111827',
        paper: '#ffffff',
        line: '#d7dde6',
        brand: {
          50: '#eef2ff',
          500: '#2F4FDC',
          600: '#2946c7',
          700: '#233cae'
        },
        signal: {
          green: '#22A06B',
          amber: '#D97706',
          red: '#dc2626',
          blue: '#2F4FDC',
          cyan: '#0891b2'
        }
      },
      boxShadow: {
        panel: '0 1px 2px rgba(15, 23, 42, 0.04)',
        insetline: 'inset 3px 0 0 rgba(47, 79, 220, 0.95)'
      }
    }
  },
  plugins: []
};
