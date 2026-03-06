import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Both maplibre-gl (pure ESM + web workers) and react-map-gl must be
  // excluded from esbuild pre-bundling in Vite 4, otherwise maplibregl
  // is undefined at runtime ("Cannot read properties of undefined 'Map'").
  optimizeDeps: {
    exclude: ['maplibre-gl', 'react-map-gl'],
  },
})
