import { useEffect, useRef, useState } from 'react'
import { getProgress, runGithubCi, runLocalCi } from '../api/ci'

export function useCiProgress(onComplete) {
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState(null)
  const timerRef = useRef(null)

  const startPolling = () => {
    timerRef.current = setInterval(async () => {
      try {
        const p = await getProgress()
        setProgress(p)
        if (!p.active) {
          clearInterval(timerRef.current)
          timerRef.current = null
          setRunning(false)
          setProgress(null)
          if (p.error) setError(p.error)
          else onComplete()
        }
      } catch {
        /* transient poll failure — keep polling */
      }
    }, 1500)
  }

  useEffect(() => {
    getProgress().then(p => {
      if (p.active) {
        setRunning(true)
        setProgress(p)
        startPolling()
      }
    }).catch(() => {})

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  const startRun = async () => {
    setError(null)
    setProgress(null)
    setRunning(true)
    try {
      const res = await runLocalCi()
      if (res && res.started === false) {
        setError('An analysis is already running')
        setRunning(false)
        return
      }
    } catch (e) {
      setError(e.message)
      setRunning(false)
      return
    }
    startPolling()
  }

  const startGithubRun = async (repoName) => {
    setError(null)
    setProgress(null)
    setRunning(true)
    try {
      const res = await runGithubCi(repoName)
      if (res && res.started === false) {
        setError('An analysis is already running')
        setRunning(false)
        return
      }
    } catch (e) {
      setError(e.message)
      setRunning(false)
      return
    }
    startPolling()
  }

  return { running, progress, error, setError, startRun, startGithubRun }
}
