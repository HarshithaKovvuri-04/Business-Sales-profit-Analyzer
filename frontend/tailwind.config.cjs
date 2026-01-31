module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  // theme is single default; dark mode removed
  theme: {
    extend: {
      colors: {
        fintech: {
          bg: '#F5F7FB',
          surface: '#FFFFFF',
          accent: '#6C8CFF',
          accent2: '#7B8BFF',
          success: '#3BCF8E',
          danger: '#FF6B6B',
          muted: '#9AA4C0'
        }
      },
      borderRadius: {
        lg: '12px',
        xl: '16px'
      },
      boxShadow: {
        soft: '0 10px 30px rgba(28,31,50,0.06)',
        elevated: '0 6px 18px rgba(28,31,50,0.08)'
      }
    },
  },
  plugins: [],
}
