import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const LONG_TIMEOUT = 1800000
const FRONTEND_DIR = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_URL || 'http://localhost:8000'
  const proxy = Object.fromEntries(
    ['/github', '/auth', '/tokens', '/repomaps', '/ci', '/diagram'].map(path => [
      path,
      { target: apiTarget, changeOrigin: true, timeout: LONG_TIMEOUT, proxyTimeout: LONG_TIMEOUT },
    ])
  )
  proxy['/brainstorm-api'] = {
    target: env.BRAINSTORM_API_URL || process.env.BRAINSTORM_API_URL || 'http://localhost:8010',
    changeOrigin: true,
    timeout: LONG_TIMEOUT,
    proxyTimeout: LONG_TIMEOUT,
    rewrite: p => p.replace(/^\/brainstorm-api/, ''),
  }
  const brainstormDir = process.env.BRAINSTORM_DIR || env.BRAINSTORM_DIR
    || path.resolve(FRONTEND_DIR, '../../Brainstorm')
  const embedEntry = path.join(brainstormDir, 'apps/web/src/embed/index.ts')
  const embedStub = path.resolve(FRONTEND_DIR, 'src/components/brainstorm/BrainstormUnavailable.jsx')
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
    resolve: {
      alias: { '@brainstorm/embed': fs.existsSync(embedEntry) ? embedEntry : embedStub },
      dedupe: ['react', 'react-dom'],
    },
    optimizeDeps: { include: ['elkjs', 'lucide-react'] },
    server: {
      fs: { allow: [FRONTEND_DIR, brainstormDir] },
      allowedHosts: ['.trycloudflare.com'],
      proxy,
    },
  }
})
