import { useEffect, useState } from 'react'
import { getRepoHome } from '../api/repomaps'

export function useRepoHome(repo, fixtureUrl) {
  const [home, setHome] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!fixtureUrl && !repo) return undefined
    let live = true
    setLoading(true)
    setError(null)
    const req = fixtureUrl ? fetch(fixtureUrl).then(r => r.json()) : getRepoHome(repo)
    req
      .then(data => { if (live) setHome(data) })
      .catch(e => { if (live) setError(e.message) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [repo, fixtureUrl])

  return { home, loading, error }
}
