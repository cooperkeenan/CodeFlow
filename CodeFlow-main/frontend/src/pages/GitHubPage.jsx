import { useGitHub } from '../hooks/useGithub'

export default function GitHubPage({ onBack, onResult, loading, onSelect }) {
  const { accessToken, repos, loading: reposLoading, login } = useGitHub()

  if (!accessToken) {
    return (
      <main className="page">
        <button className="back" onClick={onBack}>← back</button>
        <h1 className="page-title">Connect GitHub</h1>
        <p className="page-sub">Authorise access to analyse your repositories</p>
        <button className="btn-primary" onClick={login}>
          Authorise with GitHub
        </button>
      </main>
    )
  }

  if (reposLoading) {
    return (
      <main className="page">
        <div className="loading-bar"><span /></div>
      </main>
    )
  }

  return (
    <main className="page">
      <button className="back" onClick={onBack}>← back</button>
      <h1 className="page-title">Select Repository</h1>
      <p className="page-sub">{repos.length} Python repositories</p>
      {loading && <div className="loading-bar"><span /></div>}
      <div className="card-list">
        {repos.map(repo => (
          <button
            key={repo.full_name}
            className="card"
            disabled={loading}
            onClick={() => onSelect(repo, accessToken)}
          >
            <span className="card-title">{repo.name}</span>
            <span className="card-sub">{repo.description || '—'}</span>
          </button>
        ))}
      </div>
    </main>
  )
}