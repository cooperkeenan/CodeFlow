import { useEffect, useState } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import { useAnalysis } from './hooks/useAnalysis'
import { getSessionToken, saveSession, saveGithubToken } from './api/session'
import { exchangeCode, linkGithub } from './api/github'
import { RepoMapsProvider } from './hooks/RepoMapsContext'
import RequireAuth from './components/RequireAuth'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import DashboardPage from './pages/DashboardPage'
import SettingsPage from './pages/SettingsPage'
import FlowPage from './pages/FlowPage'

export default function App() {
  const navigate = useNavigate()
  const { analysis, reset, show } = useAnalysis()
  const [oauthPending, setOauthPending] = useState(
    () => new URLSearchParams(window.location.search).has('code')
  )

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    if (!code) return
    const finish = (path) => { window.history.replaceState({}, '', '/'); setOauthPending(false); navigate(path) }
    if (getSessionToken()) {
      linkGithub(code).then(() => finish('/settings')).catch(() => finish('/settings'))
    } else {
      exchangeCode(code)
        .then(d => { saveSession(d.session_token, d.user); saveGithubToken(d.github_access_token); finish('/') })
        .catch(() => finish('/login'))
    }
  }, [])

  const openMap = (map) => { show(map); navigate('/flow') }

  if (oauthPending) {
    return (
      <Box sx={{ display: 'grid', placeItems: 'center', minHeight: '100vh' }}>
        <CircularProgress color="primary" />
      </Box>
    )
  }

  return (
    <RepoMapsProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <DashboardPage onOpenMap={openMap} />
            </RequireAuth>
          }
        />
        <Route path="/settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />
        <Route
          path="/flow"
          element={
            <RequireAuth>
              {analysis
                ? <FlowPage analysis={analysis} onBack={() => { reset(); navigate('/') }} />
                : <Navigate to="/" replace />}
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </RepoMapsProvider>
  )
}
