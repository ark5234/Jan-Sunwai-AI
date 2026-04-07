import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['leaflet', 'leaflet.heat'],
  },
  build: {
    sourcemap: false,
    target: 'es2020',
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return null
          if (id.includes('react-router') || id.includes('/react/') || id.includes('/react-dom/')) {
            return 'vendor-react'
          }
          if (id.includes('leaflet') || id.includes('maplibre') || id.includes('react-leaflet') || id.includes('react-map-gl')) {
            return 'vendor-maps'
          }
          if (id.includes('lucide-react')) {
            return 'vendor-ui'
          }
          return 'vendor'
        },
      },
    },
  },
})
