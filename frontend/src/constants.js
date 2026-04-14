export const API_URL = 'http://localhost:8000'
export const GITHUB_CLIENT_ID = 'Ov23liff91VGCpUNWcXc'
export const REDIRECT_URI = 'http://localhost:5173'

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