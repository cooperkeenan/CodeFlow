import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_URL || 'http://localhost:8000'
  const proxy = Object.fromEntries(
    ['/analyse', '/github', '/code', '/auth', '/tokens', '/repomaps', '/ci'].map(path => [
      path,
      { target: apiTarget, changeOrigin: true },
    ])
  )
  return {
    plugins: [react()],
    server: {
      allowedHosts: ['.trycloudflare.com'],
      proxy,
    },
  }
})
