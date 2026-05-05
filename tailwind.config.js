/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        coral: '#FF6B6B',
        'coral-lt': '#FF8E8E',
        'coral-dk': '#E85555',
        teal: '#00C9A7',
        'teal-lt': '#6EECD6',
        amber: '#FFB830',
        'amber-lt': '#FFD980',
        indigo: '#5C6BC0',
        'indigo-lt': '#7986CB',
        violet: '#8B5CF6',
        surface: '#FFFFFF',
        bg: '#F2F4F8',
        bg2: '#E8EBF2',
        sidebar: '#1A1D2E',
      },
      borderRadius: {
        sm: '10px',
        md: '14px',
        lg: '20px',
        xl: '28px',
      },
      boxShadow: {
        'sm': '0 1px 4px rgba(26,29,46,.06)',
        'md': '0 4px 16px rgba(26,29,46,.09)',
        'lg': '0 12px 40px rgba(26,29,46,.12)',
      },
      fontFamily: {
        sans: ["'DM Sans'", "'Noto Sans SC'", 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.25s ease',
        'pulse': 'pulse 2s infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
      },
    },
  },
  plugins: [],
}
