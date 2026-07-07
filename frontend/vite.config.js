import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      '/analyse': { target: 'http://localhost:8000', changeOrigin: true },
      '/github': { target: 'http://localhost:8000', changeOrigin: true },
      '/code': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
