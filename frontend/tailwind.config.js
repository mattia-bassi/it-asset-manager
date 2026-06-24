/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'asset-manager-yellow': '#FFDD0F',
        'asset-manager-gray': '#515D64',
        'asset-manager-yellow-hover': '#E6C60E',
        'asset-manager-gray-hover': '#3D464A',
        'primary': '#FFDD0F',
        'primary-hover': '#E6C60E',
        'secondary': '#515D64',
        'secondary-hover': '#3D464A',
      },
    },
  },
  plugins: [],
}
