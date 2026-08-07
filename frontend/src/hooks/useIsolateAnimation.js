import { useEffect, useRef, useState } from 'react'

const SWAP_AT = 0.62

const IDLE = { id: null, grown: false, dashed: false, animating: false, swapped: false }

export function useIsolateAnimation(isolatedId, dimMs, expandMs) {
  const [phase, setPhase] = useState(IDLE)
  const timers = useRef([])

  useEffect(() => {
    timers.current.forEach(clearTimeout)
    timers.current = []
    const schedule = (fn, ms) => timers.current.push(setTimeout(fn, ms))
    const open = (grown, dashed) => ({ id: isolatedId, grown, dashed, animating: true, swapped: false })

    if (isolatedId) {
      setPhase(open(false, false))
      schedule(() => setPhase(open(true, false)), dimMs)
      schedule(() => setPhase(open(true, true)), dimMs + expandMs / 2)
      schedule(
        () => setPhase({ id: isolatedId, grown: true, dashed: true, animating: false, swapped: false }),
        dimMs + expandMs,
      )
    } else {
      setPhase(prev =>
        prev.id
          ? { id: prev.id, grown: false, dashed: true, animating: true, swapped: false }
          : IDLE,
      )
      schedule(
        () => setPhase(prev => (prev.id ? { ...prev, swapped: true } : prev)),
        expandMs * SWAP_AT,
      )
      schedule(() => setPhase(IDLE), expandMs)
    }

    return () => {
      timers.current.forEach(clearTimeout)
      timers.current = []
    }
  }, [isolatedId, dimMs, expandMs])

  return phase
}
