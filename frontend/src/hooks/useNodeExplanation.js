import { useEffect, useState } from 'react'
import { explainNode } from '../api/explain'
import { useExplanationCache } from './ExplanationCacheContext'

export function useNodeExplanation(repo, nodeId) {
  const cache = useExplanationCache()
  const [explanation, setExplanation] = useState(null)
  const [sources, setSources] = useState({})
  const [steps, setSteps] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!repo || !nodeId) {
      setExplanation(null)
      setSources({})
      setSteps({})
      setLoading(false)
      setError(null)
      return
    }

    const key = `${repo}::${nodeId}`
    const cached = cache?.get(key)
    if (cached) {
      setExplanation(cached.explanation)
      setSources(cached.sources)
      setSteps(cached.steps ?? {})
      setLoading(false)
      setError(null)
      return
    }

    let live = true
    setLoading(true)
    setError(null)
    setExplanation(null)
    setSources({})
    setSteps({})
    explainNode(repo, nodeId)
      .then(data => {
        if (!live) return
        const explanationData = data.explanation
        const sourcesData = data.sources ?? {}
        const stepsData = data.steps ?? {}
        setExplanation(explanationData)
        setSources(sourcesData)
        setSteps(stepsData)
        cache?.set(key, { explanation: explanationData, sources: sourcesData, steps: stepsData })
      })
      .catch(e => { if (live) setError(e.message) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [repo, nodeId, cache])

  return { explanation, sources, steps, loading, error }
}
