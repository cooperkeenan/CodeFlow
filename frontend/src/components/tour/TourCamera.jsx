import { useEffect } from 'react'
import { useReactFlow, useStore } from 'reactflow'
import { boundsOf } from '../flow/nodeBounds'
import { shotFor, zoomFor, SOLO_SPAN } from './shotTypes'

const SETTLE_MS = 40

function spanOf(bounds, shot) {
  const spanX = bounds.maxX - bounds.minX
  const spanY = bounds.maxY - bounds.minY
  if (shot !== 'detail') return { cx: (bounds.minX + bounds.maxX) / 2, cy: (bounds.minY + bounds.maxY) / 2, x: spanX, y: spanY }
  return {
    cx: (bounds.minX + bounds.maxX) / 2,
    cy: (bounds.minY + bounds.maxY) / 2,
    x: Math.max(spanX, SOLO_SPAN.x),
    y: Math.max(spanY, SOLO_SPAN.y),
  }
}

export default function TourCamera({ focusIds, tick, bottomInset = 0, shot }) {
  const { getNode, setViewport } = useReactFlow()
  const width = useStore(s => s.width)
  const height = useStore(s => s.height)

  useEffect(() => {
    if (!width || !height) return undefined
    const frame = setTimeout(() => {
      const nodes = (focusIds ?? []).map(getNode).filter(Boolean)
      if (!nodes.length) return
      const usableW = Math.max(240, width)
      const usableH = Math.max(240, height - bottomInset)
      const resolved = shotFor(shot)
      const { cx, cy, x: spanX, y: spanY } = spanOf(boundsOf(nodes), shot)
      const zoom = zoomFor(resolved, { x: spanX, y: spanY }, { width: usableW, height: usableH })
      setViewport(
        { x: usableW / 2 - cx * zoom, y: usableH / 2 - cy * zoom, zoom },
        { duration: resolved.duration },
      )
    }, SETTLE_MS)
    return () => clearTimeout(frame)
  }, [tick, focusIds, bottomInset, shot, getNode, setViewport, width, height])

  return null
}
