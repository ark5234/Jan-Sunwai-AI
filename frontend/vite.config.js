import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Exclude maplibre-gl from Vite pre-bundling — esbuild injects
  // __publicField helpers that are not available at runtime otherwise.
  optimizeDeps: {
    exclude: ['maplibre-gl'],
  },
})
