const { join } = require('path');

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'aws-dark-blue': '#232F3E',
        'aws-dark-blue-light': '#31465F',
        'aws-dark-blue-dark': '#1A242F',
        'aws-orange': '#FF9900',
        'aws-orange-light': '#FFA827',
        'aws-orange-dark': '#E68A00',
      },
    },
  },
  plugins: [],
};
