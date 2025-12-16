import { colors, shadows, animations } from './packages/ui/src/theme'

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    './packages/ui/src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: colors.primary,
        secondary: colors.secondary,
        accent: colors.accent,
        'bg-dark': colors.bgDark,
        'surface-dark': colors.surfaceDark,
        'border-dark': colors.borderDark,
      },
      boxShadow: {
        'soft-xl': shadows.softXl,
      },
      keyframes: {
        ...animations.keyframes,
      },
      animation: {
        ...animations.animation,
      },
    },
  },
  plugins: [],
}


