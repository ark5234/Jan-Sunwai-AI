// vite.config.js
import { defineConfig } from "file:///C:/Users/Vikra/OneDrive/Desktop/Jan-Sunwai%20AI/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///C:/Users/Vikra/OneDrive/Desktop/Jan-Sunwai%20AI/frontend/node_modules/@vitejs/plugin-react/dist/index.mjs";
var vite_config_default = defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy API calls to FastAPI backend during development
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      // Proxy static uploads (images) to backend during development
      "/uploads": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  },
  optimizeDeps: {
    include: ["leaflet", "leaflet.heat"]
  },
  build: {
    sourcemap: false,
    target: "es2020",
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules"))
            return null;
          if (id.includes("react-router") || id.includes("/react/") || id.includes("/react-dom/")) {
            return "vendor-react";
          }
          if (id.includes("leaflet") || id.includes("maplibre") || id.includes("react-leaflet") || id.includes("react-map-gl")) {
            return "vendor-maps";
          }
          if (id.includes("lucide-react")) {
            return "vendor-ui";
          }
          return "vendor";
        }
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxWaWtyYVxcXFxPbmVEcml2ZVxcXFxEZXNrdG9wXFxcXEphbi1TdW53YWkgQUlcXFxcZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkM6XFxcXFVzZXJzXFxcXFZpa3JhXFxcXE9uZURyaXZlXFxcXERlc2t0b3BcXFxcSmFuLVN1bndhaSBBSVxcXFxmcm9udGVuZFxcXFx2aXRlLmNvbmZpZy5qc1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vQzovVXNlcnMvVmlrcmEvT25lRHJpdmUvRGVza3RvcC9KYW4tU3Vud2FpJTIwQUkvZnJvbnRlbmQvdml0ZS5jb25maWcuanNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xuaW1wb3J0IHJlYWN0IGZyb20gJ0B2aXRlanMvcGx1Z2luLXJlYWN0J1xuXG4vLyBodHRwczovL3ZpdGVqcy5kZXYvY29uZmlnL1xuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcbiAgcGx1Z2luczogW3JlYWN0KCldLFxuICBzZXJ2ZXI6IHtcbiAgICBwcm94eToge1xuICAgICAgLy8gUHJveHkgQVBJIGNhbGxzIHRvIEZhc3RBUEkgYmFja2VuZCBkdXJpbmcgZGV2ZWxvcG1lbnRcbiAgICAgICcvYXBpJzoge1xuICAgICAgICB0YXJnZXQ6ICdodHRwOi8vbG9jYWxob3N0OjgwMDAnLFxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWUsXG4gICAgICB9LFxuICAgICAgLy8gUHJveHkgc3RhdGljIHVwbG9hZHMgKGltYWdlcykgdG8gYmFja2VuZCBkdXJpbmcgZGV2ZWxvcG1lbnRcbiAgICAgICcvdXBsb2Fkcyc6IHtcbiAgICAgICAgdGFyZ2V0OiAnaHR0cDovL2xvY2FsaG9zdDo4MDAwJyxcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxuICAgICAgfSxcbiAgICB9LFxuICB9LFxuICBvcHRpbWl6ZURlcHM6IHtcbiAgICBpbmNsdWRlOiBbJ2xlYWZsZXQnLCAnbGVhZmxldC5oZWF0J10sXG4gIH0sXG4gIGJ1aWxkOiB7XG4gICAgc291cmNlbWFwOiBmYWxzZSxcbiAgICB0YXJnZXQ6ICdlczIwMjAnLFxuICAgIGNodW5rU2l6ZVdhcm5pbmdMaW1pdDogOTAwLFxuICAgIHJvbGx1cE9wdGlvbnM6IHtcbiAgICAgIG91dHB1dDoge1xuICAgICAgICBtYW51YWxDaHVua3MoaWQpIHtcbiAgICAgICAgICBpZiAoIWlkLmluY2x1ZGVzKCdub2RlX21vZHVsZXMnKSkgcmV0dXJuIG51bGxcbiAgICAgICAgICBpZiAoaWQuaW5jbHVkZXMoJ3JlYWN0LXJvdXRlcicpIHx8IGlkLmluY2x1ZGVzKCcvcmVhY3QvJykgfHwgaWQuaW5jbHVkZXMoJy9yZWFjdC1kb20vJykpIHtcbiAgICAgICAgICAgIHJldHVybiAndmVuZG9yLXJlYWN0J1xuICAgICAgICAgIH1cbiAgICAgICAgICBpZiAoaWQuaW5jbHVkZXMoJ2xlYWZsZXQnKSB8fCBpZC5pbmNsdWRlcygnbWFwbGlicmUnKSB8fCBpZC5pbmNsdWRlcygncmVhY3QtbGVhZmxldCcpIHx8IGlkLmluY2x1ZGVzKCdyZWFjdC1tYXAtZ2wnKSkge1xuICAgICAgICAgICAgcmV0dXJuICd2ZW5kb3ItbWFwcydcbiAgICAgICAgICB9XG4gICAgICAgICAgaWYgKGlkLmluY2x1ZGVzKCdsdWNpZGUtcmVhY3QnKSkge1xuICAgICAgICAgICAgcmV0dXJuICd2ZW5kb3ItdWknXG4gICAgICAgICAgfVxuICAgICAgICAgIHJldHVybiAndmVuZG9yJ1xuICAgICAgICB9LFxuICAgICAgfSxcbiAgICB9LFxuICB9LFxufSlcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBb1csU0FBUyxvQkFBb0I7QUFDalksT0FBTyxXQUFXO0FBR2xCLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVMsQ0FBQyxNQUFNLENBQUM7QUFBQSxFQUNqQixRQUFRO0FBQUEsSUFDTixPQUFPO0FBQUE7QUFBQSxNQUVMLFFBQVE7QUFBQSxRQUNOLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxNQUNoQjtBQUFBO0FBQUEsTUFFQSxZQUFZO0FBQUEsUUFDVixRQUFRO0FBQUEsUUFDUixjQUFjO0FBQUEsTUFDaEI7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUFBLEVBQ0EsY0FBYztBQUFBLElBQ1osU0FBUyxDQUFDLFdBQVcsY0FBYztBQUFBLEVBQ3JDO0FBQUEsRUFDQSxPQUFPO0FBQUEsSUFDTCxXQUFXO0FBQUEsSUFDWCxRQUFRO0FBQUEsSUFDUix1QkFBdUI7QUFBQSxJQUN2QixlQUFlO0FBQUEsTUFDYixRQUFRO0FBQUEsUUFDTixhQUFhLElBQUk7QUFDZixjQUFJLENBQUMsR0FBRyxTQUFTLGNBQWM7QUFBRyxtQkFBTztBQUN6QyxjQUFJLEdBQUcsU0FBUyxjQUFjLEtBQUssR0FBRyxTQUFTLFNBQVMsS0FBSyxHQUFHLFNBQVMsYUFBYSxHQUFHO0FBQ3ZGLG1CQUFPO0FBQUEsVUFDVDtBQUNBLGNBQUksR0FBRyxTQUFTLFNBQVMsS0FBSyxHQUFHLFNBQVMsVUFBVSxLQUFLLEdBQUcsU0FBUyxlQUFlLEtBQUssR0FBRyxTQUFTLGNBQWMsR0FBRztBQUNwSCxtQkFBTztBQUFBLFVBQ1Q7QUFDQSxjQUFJLEdBQUcsU0FBUyxjQUFjLEdBQUc7QUFDL0IsbUJBQU87QUFBQSxVQUNUO0FBQ0EsaUJBQU87QUFBQSxRQUNUO0FBQUEsTUFDRjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
