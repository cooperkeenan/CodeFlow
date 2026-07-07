import { useState } from 'react'
import { useAnalysis } from './hooks/useAnalysis'
import { getSessionToken } from './api/session'
import HomePage from './pages/HomePage'
import GitHubPage from './pages/GitHubPage'
import LocalPage from './pages/LocalPage'
import AccountPage from './pages/AccountPage'
import DiagramPage from './pages/DiagramPage'

export default function App() {
  const [view, setView] = useState(
    () => new URLSearchParams(window.location.search).has('code') ? 'github' : 'home'
  )
  const { analysis, loading, error, run, reset, show } = useAnalysis()

  const goHome = () => { reset(); setView('home') }

  const openAccount = () => setView(getSessionToken() ? 'account' : 'github')

  const handleOpenMap = (map) => { show(map); setView('diagram') }

  const handleGitHubSelect = async (repo, accessToken) => {
    const result = await run('/analyse', { access_token: accessToken, repo_name: repo.full_name })
    if (result) setView('diagram')
  }

  const handleLocalRun = async (endpoint) => {
    const result = await run(endpoint)
    if (result) setView('diagram')
  }

  if (view === 'diagram' && analysis) {
    return <DiagramPage analysis={analysis} onBack={goHome} />
  }

  if (view === 'github') {
    return (
      <GitHubPage
        onBack={goHome}
        loading={loading}
        onSelect={handleGitHubSelect}
      />
    )
  }

  if (view === 'local') {
    return (
      <LocalPage
        onBack={goHome}
        loading={loading}
        onRun={handleLocalRun}
      />
    )
  }

  if (view === 'account') {
    return <AccountPage onBack={goHome} onOpenMap={handleOpenMap} />
  }

  return (
    <HomePage
      onGitHub={() => setView('github')}
      onLocal={() => setView('local')}
      onAccount={openAccount}
    />
  )
}