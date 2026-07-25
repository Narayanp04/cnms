import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        timeout: 60000,
        proxyTimeout: 60000,
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            console.error('[proxy error]', err.message);
            if (!res.headersSent) {
              res.writeHead(502, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ detail: 'Backend connection error. Please try again.' }));
            }
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            proxyReq.setHeader('Connection', 'keep-alive');
          });
        }
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react/') || id.includes('node_modules/react-dom/') || id.includes('node_modules/react-router-dom/')) {
            return 'vendor';
          }
          if (id.includes('node_modules/echarts') || id.includes('node_modules/recharts')) {
            return 'charts';
          }
          if (id.includes('node_modules/react-icons/') || id.includes('node_modules/framer-motion/')) {
            return 'ui';
          }
        }
      }
    }
  }
})
