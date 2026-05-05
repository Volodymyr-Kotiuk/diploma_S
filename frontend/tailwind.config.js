/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        ink: '#111827',
        surface: '#f5f6f8',
        graphite: '#1f2937',
        console: '#111827',
        paper: '#ffffff',
        line: '#cbd5e1',
        brand: {
          50: '#eff6ff',
          500: '#1d4ed8',
          600: '#1e40af',
          700: '#1e3a8a'
        },
        signal: {
          green: '#16a34a',
          amber: '#ca8a04',
          red: '#dc2626',
          blue: '#2563eb',
          cyan: '#0891b2'
        }
      },
      boxShadow: {
        panel: 'none',
        insetline: 'inset 4px 0 0 rgba(37, 99, 235, 0.95)'
      }
    }
  },
  plugins: []
};
