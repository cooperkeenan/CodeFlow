import React, { useState, useEffect } from 'react'
import GitHubFlow from './GitHubFlow'
import LocalFlow from './LocalFlow'
import DiagramViewer from './DiagramViewer'
import './index.css'

const API_URL = 'http://localhost:8000'

export default function App() {
  const [view, setView] = useState('home')
  const [accessToken, setAccessToken] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    if (code && !accessToken) {
      fetch(`${API_URL}/github/auth/callback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
        .then(r => r.json())
        .then(d => {
          setAccessToken(d.access_token)
          setView('github')
          window.history.replaceState({}, '', '/')
        })
    }
  }, [])

  const runAnalysis = async (endpoint, body = null) => {
    setLoading(true)
    setLoadingMsg('Running analysis...')
    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setAnalysis(data)
      setView('diagram')
    } catch (e) {
      alert(`Analysis failed: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  if (view === 'diagram') {
    return <DiagramViewer analysis={analysis} onBack={() => setView('home')} />
  }

  if (view === 'github') {
    return (
      <GitHubFlow
        accessToken={accessToken}
        loading={loading}
        onRepoSelected={repo => runAnalysis('/analyse', {
          access_token: accessToken,
          repo_name: repo.full_name,
        })}
        onBack={() => setView('home')}
      />
    )
  }

  if (view === 'local') {
    return (
      <LocalFlow
        loading={loading}
        loadingMsg={loadingMsg}
        onRun={stage => {
          const endpoints = {
            profiler: '/analyse/local',
            tracer:   '/analyse/local/from-profile',
            render:   '/analyse/local/from-trace',
          }
          runAnalysis(endpoints[stage])
        }}
        onBack={() => setView('home')}
      />
    )
  }

  return (
    <div className="home">
      <div className="home-inner">
        <div className="logo">
          <span className="logo-bracket">{'//'}</span>
          <span className="logo-text">CodeFlow</span>
        </div>
        <p className="tagline">Architecture diagrams from source code</p>
        <div className="home-actions">
          <button className="btn-primary" onClick={() => setView('github')}>
            <span className="btn-icon">⬡</span>
            Connect GitHub
          </button>
          <button className="btn-secondary" onClick={() => setView('local')}>
            <span className="btn-icon">◈</span>
            Generate from Output
          </button>
        </div>
      </div>
    </div>
  )
}
