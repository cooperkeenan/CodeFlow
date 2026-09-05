import { useEffect, useState } from 'react'
import { getFlowGraph } from '../api/flow'

export function useFlowGraph(repo, fixtureUrl, entry) {
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!fixtureUrl && !repo) return
    let live = true
    setLoading(true)
    setError(null)
    const request = fixtureUrl
      ? fetch(fixtureUrl).then(res => res.json())
      : getFlowGraph(repo, entry)
    request
      .then(data => { if (live) setPayload(data) })
      .catch(e => { if (live) setError(e.message) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [repo, fixtureUrl, entry])

  return { payload, loading, error }
}
