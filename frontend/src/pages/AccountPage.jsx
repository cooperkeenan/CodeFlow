import { useEffect, useState } from 'react'
import { createToken, listTokens, revokeToken } from '../api/tokens'
import { getRepoMap, listRepoMaps } from '../api/repomaps'
import { getUser } from '../api/session'

export default function AccountPage({ onBack, onOpenMap }) {
  const user = getUser()
  const [maps, setMaps] = useState([])
  const [tokens, setTokens] = useState([])
  const [newToken, setNewToken] = useState(null)
  const [name, setName] = useState('')
  const [error, setError] = useState(null)

  const refresh = () => {
    listRepoMaps().then(d => setMaps(d.repo_maps)).catch(e => setError(e.message))
    listTokens().then(setTokens).catch(e => setError(e.message))
  }

  useEffect(refresh, [])

  const open = (repo) => {
    getRepoMap(repo).then(d => onOpenMap(d.map)).catch(e => setError(e.message))
  }

  const create = () => {
    if (!name.trim()) return
    createToken(name.trim())
      .then(t => { setNewToken(t); setName(''); refresh() })
      .catch(e => setError(e.message))
  }

  const revoke = (id) => {
    revokeToken(id).then(refresh).catch(e => setError(e.message))
  }

  return (
    <main className="page">
      <button className="back" onClick={onBack}>← back</button>
      <h1 className="page-title">Account</h1>
      {user && <p className="page-sub">Signed in as {user.github_login}</p>}
      {error && <p className="error">{error}</p>}

      <h2 className="page-sub">Saved RepoMaps</h2>
      <div className="card-list">
        {maps.length === 0 && <p className="page-sub">No saved RepoMaps yet.</p>}
        {maps.map(m => (
          <button key={m.repo} className="card" onClick={() => open(m.repo)}>
            <span className="card-badge">{m.source}</span>
            <span className="card-title">{m.repo}</span>
            <span className="card-sub">updated {new Date(m.updated_at).toLocaleString()}</span>
          </button>
        ))}
      </div>

      <h2 className="page-sub">API tokens</h2>
      {newToken && (
        <div className="token-reveal">
          <span className="card-sub">Copy this token now — it is shown only once:</span>
          <code className="token-value">{newToken.token}</code>
        </div>
      )}
      <div className="token-create">
        <input
          className="token-input"
          placeholder="Token name (e.g. ci)"
          value={name}
          onChange={e => setName(e.target.value)}
        />
        <button className="btn-primary" onClick={create}>Create token</button>
      </div>
      <div className="card-list">
        {tokens.map(t => (
          <div key={t.id} className="token-row">
            <span className="card-title">{t.name || '(unnamed)'}</span>
            <span className="card-sub">{t.prefix}…</span>
            {t.revoked_at
              ? <span className="card-sub">revoked</span>
              : <button className="btn-ghost" onClick={() => revoke(t.id)}>Revoke</button>}
          </div>
        ))}
      </div>
    </main>
  )
}
