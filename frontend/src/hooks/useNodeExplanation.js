import { useEffect, useState } from 'react'
import { explainNode } from '../api/explain'
import { useExplanationCache } from './ExplanationCacheContext'

export function useNodeExplanation(repo, nodeId) {
  const cache = useExplanationCache()
  const [explanation, setExplanation] = useState(null)
  const [sources, setSources] = useState({})
  const [sequence, setSequence] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!repo || !nodeId) {
      setExplanation(null)
      setSources({})
      setSequence([])
      setLoading(false)
      setError(null)
      return
    }

    const key = `${repo}::${nodeId}`
    const cached = cache?.get(key)
    if (cached) {
      setExplanation(cached.explanation)
      setSources(cached.sources)
      setSequence(cached.sequence ?? [])
      setLoading(false)
      setError(null)
      return
    }

    let live = true
    setLoading(true)
    setError(null)
    setExplanation(null)
    setSources({})
    setSequence([])
    explainNode(repo, nodeId)
      .then(data => {
        if (!live) return
        const explanationData = data.explanation
        const sourcesData = data.sources ?? {}
        const sequenceData = data.sequence ?? []
        setExplanation(explanationData)
        setSources(sourcesData)
        setSequence(sequenceData)
        cache?.set(key, { explanation: explanationData, sources: sourcesData, sequence: sequenceData })
      })
      .catch(e => { if (live) setError(e.message) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [repo, nodeId, cache])

  return { explanation, sources, sequence, loading, error }
}
