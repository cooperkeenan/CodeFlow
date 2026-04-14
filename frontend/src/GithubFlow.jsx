import React, { useState, useEffect } from 'react'

const API_URL = 'http://localhost:8000'
const GITHUB_CLIENT_ID = 'Ov23liff91VGCpUNWcXc'

export default function GitHubFlow({ accessToken, loading, onRepoSelected, onBack }) {
  const [repos, setRepos] = useState([])
  const [fetching, setFetching] = useState(false)

  useEffect(() => {
    if (!accessToken) return
    setFetching(true)
    fetch(`${API_URL}/github/repos?access_token=${accessToken}`)
      .then(r => r.json())
      .then(d => { setRepos(d.repositories); setFetching(false) })
  }, [accessToken])

  if (!accessToken) {
    return (
      <div className="flow-page">
        <button className="back-btn" onClick={onBack}>← back</button>
        <h2 className="flow-title">Connect GitHub</h2>
        <p className="flow-sub">Authorise access to analyse your repositories</p>
        <button
          className="btn-primary"
          onClick={() => {
            window.location.href = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=http://localhost:5173&scope=repo`
          }}
        >
          Authorise with GitHub
        </button>
      </div>
    )
  }

  if (fetching) return <div className="flow-page"><p className="flow-sub">Loading repositories...</p></div>

  const pythonRepos = repos.filter(r => r.language === 'Python')

  return (
    <div className="flow-page">
      <button className="back-btn" onClick={onBack}>← back</button>
      <h2 className="flow-title">Select Repository</h2>
      <p className="flow-sub">{pythonRepos.length} Python repositories found</p>
      {loading && <div className="loading-bar"><span /></div>}
      <div className="repo-list">
        {pythonRepos.map(repo => (
          <button
            key={repo.full_name}
            className="repo-card"
            disabled={loading}
            onClick={() => onRepoSelected(repo)}
          >
            <span className="repo-name">{repo.name}</span>
            <span className="repo-desc">{repo.description || 'No description'}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
