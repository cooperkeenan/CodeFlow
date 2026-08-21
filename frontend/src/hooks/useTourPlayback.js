import { useCallback, useEffect, useRef, useState } from 'react'

export const STEP_MS = 4200
export const LOOP_PAUSE_MS = 2600

export function useTourPlayback(steps, autoplay = true) {
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(autoplay)
  const count = steps?.length ?? 0
  const timer = useRef(null)

  const goto = useCallback(next => {
    setIndex(prev => {
      const target = typeof next === 'function' ? next(prev) : next
      return Math.max(0, Math.min(count - 1, target))
    })
  }, [count])

  const next = useCallback(() => goto(i => i + 1), [goto])
  const prev = useCallback(() => { setPlaying(false); goto(i => i - 1) }, [goto])
  const toggle = useCallback(() => setPlaying(p => !p), [])
  const restart = useCallback(() => { setIndex(0); setPlaying(true) }, [])

  useEffect(() => {
    if (!playing || !count) return undefined
    const last = index >= count - 1
    const dwellMs = last ? LOOP_PAUSE_MS : steps[index]?.dwellMs ?? STEP_MS
    timer.current = setTimeout(() => setIndex(i => (last ? 0 : i + 1)), dwellMs)
    return () => clearTimeout(timer.current)
  }, [playing, index, count, steps])

  useEffect(() => {
    const onKey = event => {
      if (event.key === ' ') { event.preventDefault(); toggle() }
      else if (event.key === 'ArrowRight') { setPlaying(false); next() }
      else if (event.key === 'ArrowLeft') prev()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [toggle, next, prev])

  return {
    index, playing, count,
    step: count ? steps[index] : null,
    next: () => { setPlaying(false); next() },
    prev, goto: i => { setPlaying(false); goto(i) }, toggle, restart,
  }
}
