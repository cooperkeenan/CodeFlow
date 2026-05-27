export const API_URL = 'http://localhost:8000'
export const GITHUB_CLIENT_ID = 'Ov23liff91VGCpUNWcXc'
export const REDIRECT_URI = 'http://localhost:5173'

export const MODULE_PALETTE = [
  { bg: '#0a1929', border: '#0d3b6e', accent: '#35a0f1' },
  { bg: '#0a1f14', border: '#0d4a28', accent: '#35f1a0' },
  { bg: '#1f130a', border: '#4a2e0d', accent: '#f1a035' },
  { bg: '#150a1f', border: '#3a0d4a', accent: '#c035f1' },
  { bg: '#1f0a12', border: '#4a0d28', accent: '#f135a0' },
  { bg: '#0a1f1d', border: '#0d4a45', accent: '#35f1e0' },
  { bg: '#1a1f0a', border: '#3f4a0d', accent: '#d0f135' },
  { bg: '#0f0a1f', border: '#240d4a', accent: '#7a35f1' },
]

export const EXTERNAL_COLOR = { bg: '#150a1f', border: '#3a0d4a', accent: '#c035f1' }

export const STAGES = [
  {
    id: 'profiler',
    endpoint: '/analyse/local',
    badge: 'FULL PIPELINE',
    label: 'Profiler → Tracer → Render',
    desc: 'Full analysis from scratch',
  },
  {
    id: 'tracer',
    endpoint: '/analyse/local/from-profile',
    badge: 'SKIP PROFILER',
    label: 'Tracer → Render',
    desc: 'Uses stored profiler_output.json',
  },
  {
    id: 'render',
    endpoint: '/analyse/local/from-trace',
    badge: 'RENDER ONLY',
    label: 'Render',
    desc: 'Uses stored tracer_output.json',
  },
]