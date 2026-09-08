import { useEffect, useRef, useState } from 'react'
import { getProgress, runGithubCi, runLocalCi } from '../api/ci'

const POLL_MS = 1500
const EVENT_LIMIT = 500

export function useCiProgress(onComplete) {
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(null)
  const [events, setEvents] = useState([])
  const [error, setError] = useState(null)
  const timerRef = useRef(null)
  const seqRef = useRef(0)

  const stopPolling = () => {
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = null
  }

  const absorb = (snapshot) => {
    if (typeof snapshot.event_seq === 'number' && snapshot.event_seq < seqRef.current) {
      seqRef.current = 0
      setEvents([])
    }
    if (snapshot.events?.length) {
      setEvents(prev => {
        const seen = new Set(prev.map(e => e.seq))
        const fresh = snapshot.events.filter(e => !seen.has(e.seq))
        return fresh.length ? [...prev, ...fresh].slice(-EVENT_LIMIT) : prev
      })
    }
    if (typeof snapshot.event_seq === 'number') seqRef.current = snapshot.event_seq
    setProgress(snapshot)
  }

  const startPolling = () => {
    stopPolling()
    timerRef.current = setInterval(async () => {
      try {
        const snapshot = await getProgress(seqRef.current)
        absorb(snapshot)
        if (!snapshot.active) {
          stopPolling()
          setRunning(false)
          if (snapshot.error) setError(snapshot.error)
          else onComplete()
        }
      } catch {
        /* transient poll failure — keep polling */
      }
    }, POLL_MS)
  }

  useEffect(() => {
    getProgress(0).then(snapshot => {
      if (!snapshot.active) return
      setRunning(true)
      absorb(snapshot)
      startPolling()
    }).catch(() => {})

    return stopPolling
  }, [])

  const begin = async (launch) => {
    setError(null)
    setProgress(null)
    setEvents([])
    seqRef.current = 0
    setRunning(true)
    try {
      const res = await launch()
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

  const startRun = () => begin(() => runLocalCi())
  const startGithubRun = (repoName) => begin(() => runGithubCi(repoName))

  return { running, progress, events, error, setError, startRun, startGithubRun }
}
