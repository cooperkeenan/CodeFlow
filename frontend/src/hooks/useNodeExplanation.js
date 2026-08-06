import { useEffect, useState } from 'react'
import { explainNode } from '../api/explain'

export function useNodeExplanation(repo, nodeId) {
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!repo || !nodeId) {
      setExplanation(null)
      setLoading(false)
      setError(null)
      return
    }
    let live = true
    setLoading(true)
    setError(null)
    setExplanation(null)
    explainNode(repo, nodeId)
      .then(data => { if (live) setExplanation(data.explanation) })
      .catch(e => { if (live) setError(e.message) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [repo, nodeId])

  return { explanation, loading, error }
}
