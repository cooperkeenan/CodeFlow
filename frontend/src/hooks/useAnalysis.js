import { useState } from 'react'

export function useAnalysis() {
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const reset = () => { setAnalysis(null); setError(null) }

  const show = (data) => { setError(null); setAnalysis(data) }

  return { analysis, loading, error, reset, show }
}
