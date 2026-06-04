export const API_URL = 'http://localhost:8000'
export const GITHUB_CLIENT_ID = 'Ov23liff91VGCpUNWcXc'
export const REDIRECT_URI = 'http://localhost:5173'

export const MODULE_PALETTE = [
  { bg: '#0D1B2A', border: '#1B3A5C', accent: '#64B5F6' },
  { bg: '#0A1F0D', border: '#1A3A1A', accent: '#39FF14' },
  { bg: '#1F1508', border: '#4A2A0D', accent: '#FFB84D' },
  { bg: '#180A1F', border: '#3A1050', accent: '#CE93D8' },
  { bg: '#1F0A0E', border: '#4A0D1A', accent: '#FF6B6B' },
  { bg: '#0A1F1B', border: '#0D4040', accent: '#4DD0E1' },
  { bg: '#171F0A', border: '#3A4A0D', accent: '#C5E1A5' },
  { bg: '#0A0E1F', border: '#1A1D4A', accent: '#9FA8DA' },
]

export const EXTERNAL_COLOR = { bg: '#1A0A1F', border: '#400D50', accent: '#CE93D8' }

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