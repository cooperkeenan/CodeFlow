import { useState } from 'react'
import { useAnalysis } from './hooks/useAnalysis'
import HomePage from './pages/HomePage'
import GitHubPage from './pages/GithubPage'
import LocalPage from './pages/LocalPage'
import DiagramPage from './pages/DiagramPage'

export default function App() {
  const [view, setView] = useState('home')
  const { analysis, loading, error, run, reset } = useAnalysis()

  const goHome = () => { reset(); setView('home') }

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

  return (
    <HomePage
      onGitHub={() => setView('github')}
      onLocal={() => setView('local')}
    />
  )
}