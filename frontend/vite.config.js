import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

const LONG_TIMEOUT = 1800000

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_URL || 'http://localhost:8000'
  const proxy = Object.fromEntries(
    ['/github', '/auth', '/tokens', '/repomaps', '/ci', '/diagram'].map(path => [
      path,
      { target: apiTarget, changeOrigin: true, timeout: LONG_TIMEOUT, proxyTimeout: LONG_TIMEOUT },
    ])
  )
  const extendServerTimeout = {
    name: 'extend-server-timeout',
    configureServer(server) {
      if (server.httpServer) {
        server.httpServer.requestTimeout = LONG_TIMEOUT
        server.httpServer.headersTimeout = LONG_TIMEOUT
      }
    },
  }
  return {
    plugins: [react(), extendServerTimeout],
    server: {
      allowedHosts: ['.trycloudflare.com'],
      proxy,
    },
  }
})
