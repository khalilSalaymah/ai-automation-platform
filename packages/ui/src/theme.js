// Centralized design tokens shared across frontends
export const colors = {
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  accent: '#10b981',
  bgDark: '#000000', // Pure black
  surfaceDark: '#0a0a0a', // Very dark gray
  borderDark: '#1a1a1a', // Dark border
}

export const shadows = {
  softXl: '0 25px 50px -12px rgba(15,23,42,0.35)',
}

export const animations = {
  keyframes: {
    'fade-in-up': {
      '0%': { opacity: 0, transform: 'translateY(16px)' },
      '100%': { opacity: 1, transform: 'translateY(0)' },
    },
    float: {
      '0%, 100%': { transform: 'translateY(0)' },
      '50%': { transform: 'translateY(-6px)' },
    },
  },
  animation: {
    'fade-in-up': 'fade-in-up 0.35s ease-out both',
    float: 'float 4s ease-in-out infinite',
  },
}


