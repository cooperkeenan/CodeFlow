import { useState } from 'react'
import { runAnalysis } from '../api/analysis'

export function useAnalysis() {
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const run = async (endpoint, body = null) => {
    setLoading(true)
    setError(null)
    try {
      const data = await runAnalysis(endpoint, body)
      setAnalysis(data)
      return data
    } catch (e) {
      setError(e.message)
      return null
    } finally {
      setLoading(false)
    }
  }

  const reset = () => { setAnalysis(null); setError(null) }

  return { analysis, loading, error, run, reset }
}