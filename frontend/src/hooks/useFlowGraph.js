import { useEffect, useState } from 'react'
import { getFlowGraph } from '../api/flow'

export function useFlowGraph(repo) {
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!repo) return
    let live = true
    setLoading(true)
    setError(null)
    getFlowGraph(repo)
      .then(data => { if (live) setPayload(data) })
      .catch(e => { if (live) setError(e.message) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [repo])

  return { payload, loading, error }
}
