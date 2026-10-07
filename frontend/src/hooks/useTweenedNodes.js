import { useEffect, useMemo, useRef, useState } from 'react'

const DURATION = 600

function ease(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - ((-2 * t + 2) ** 3) / 2
}

function prefersReducedMotion() {
  return Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches)
}

export function useTweenedNodes(nodes, tweenKey) {
  const [run, setRun] = useState({ key: tweenKey, t: 1 })
  const shown = useRef(new Map())
  const origin = useRef(new Map())
  const mounted = useRef(false)
  const t = run.key === tweenKey ? run.t : 0

  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true
      return undefined
    }
    origin.current = shown.current
    if (prefersReducedMotion()) {
      setRun({ key: tweenKey, t: 1 })
      return undefined
    }
    let frame = 0
    let start = null
    const tick = now => {
      start ??= now
      const progress = Math.min(1, (now - start) / DURATION)
      setRun({ key: tweenKey, t: progress })
      if (progress < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [tweenKey])

  const tweened = useMemo(() => {
    if (t >= 1) return nodes
    const from = t === 0 ? shown.current : origin.current
    const k = ease(t)
    return nodes.map(n => {
      const o = from.get(n.id)
      if (!o) return n
      return {
        ...n,
        position: { x: o.x + (n.position.x - o.x) * k, y: o.y + (n.position.y - o.y) * k },
      }
    })
  }, [nodes, t])

  useEffect(() => {
    shown.current = new Map(tweened.map(n => [n.id, n.position]))
  }, [tweened])

  return { nodes: tweened, settled: t >= 1 }
}
