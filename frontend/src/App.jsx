import { useEffect, useState } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import { useAnalysis } from './hooks/useAnalysis'
import { getSessionToken, saveSession, saveGithubToken, saveUser } from './api/session'
import { exchangeCode, linkGithub } from './api/github'
import { RepoMapsProvider } from './hooks/RepoMapsContext'
import { ExplanationCacheProvider } from './hooks/ExplanationCacheContext'
import RequireAuth from './components/RequireAuth'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import DashboardPage from './pages/DashboardPage'
import RepoHomePage from './pages/RepoHomePage'
import SettingsPage from './pages/SettingsPage'
import FlowPage from './pages/FlowPage'
import TourPage from './pages/TourPage'

function fixtureAnalysis() {
  if (typeof window === 'undefined') return null
  const repo = new URLSearchParams(window.location.search).get('repo')
  return repo ? { repo } : null
}

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
      linkGithub(code)
        .then(user => { saveUser(user); finish('/settings') })
        .catch(() => finish('/settings'))
    } else {
      exchangeCode(code)
        .then(d => { saveSession(d.session_token, d.user); saveGithubToken(d.github_access_token); finish('/') })
        .catch(() => finish('/login'))
    }
  }, [])

  const openMap = (map) => { show(map); navigate('/repo') }
  const leaveFlow = () => {
    if (new URLSearchParams(window.location.search).get('entry')) navigate('/repo')
    else { reset(); navigate('/') }
  }

  if (oauthPending) {
    return (
      <Box sx={{ display: 'grid', placeItems: 'center', minHeight: '100vh' }}>
        <CircularProgress color="primary" />
      </Box>
    )
  }

  return (
    <RepoMapsProvider>
      <ExplanationCacheProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                <DashboardPage onOpenMap={openMap} />
              </RequireAuth>
            }
          />
          <Route path="/settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />
          <Route path="/tour" element={<TourPage />} />
          <Route
            path="/repo"
            element={
              <RequireAuth>
                {analysis
                  ? <RepoHomePage repo={analysis.repo} onBack={() => { reset(); navigate('/') }} />
                  : <Navigate to="/" replace />}
              </RequireAuth>
            }
          />
          <Route
            path="/repo-fixture"
            element={
              <RepoHomePage
                fixture="/fixture/repo_home.json"
                flowPath="/flow-fixture"
                repo={fixtureAnalysis()?.repo}
              />
            }
          />
          <Route
            path="/flow-fixture"
            element={
              <FlowPage
                fixture="/fixture/rendered_view.json"
                analysis={fixtureAnalysis()}
                onBack={() => navigate('/repo-fixture')}
              />
            }
          />
          <Route
            path="/flow"
            element={
              <RequireAuth>
                {analysis
                  ? <FlowPage analysis={analysis} onBack={leaveFlow} />
                  : <Navigate to="/" replace />}
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ExplanationCacheProvider>
    </RepoMapsProvider>
  )
}
