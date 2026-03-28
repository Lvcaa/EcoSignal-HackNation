/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#146940',
          container: '#348357',
          fixed: '#a4f4bf',
          'fixed-dim': '#88d7a4',
        },
        'on-primary': '#ffffff',
        'on-primary-fixed': '#002110',
        secondary: {
          DEFAULT: '#0060a8',
          container: '#47a1ff',
          fixed: '#d3e4ff',
        },
        'tertiary-fixed': '#e5e2db',
        'on-tertiary-fixed': '#1c1c18',
        'on-tertiary-fixed-variant': '#474742',
        surface: {
          DEFAULT: '#f9f9ff',
          'container-lowest': '#ffffff',
          'container-low': '#f0f3ff',
          container: '#e7eefe',
          'container-high': '#e2e8f8',
          'container-highest': '#dce2f3',
        },
        'on-surface': '#151c27',
        'on-surface-variant': '#3f4941',
        'outline-variant': '#bfc9bf',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      boxShadow: {
        card: '0 8px 24px rgba(21, 28, 39, 0.04)',
        'card-lg': '0 12px 32px rgba(21, 28, 39, 0.08)',
      },
      transitionTimingFunction: {
        'out-expo': 'cubic-bezier(0.19, 1, 0.22, 1)',
      },
    },
  },
  plugins: [],
}
