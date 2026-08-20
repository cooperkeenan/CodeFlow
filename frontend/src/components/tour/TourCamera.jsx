import { useEffect } from 'react'
import { useReactFlow, useStore } from 'reactflow'
import { boundsOf } from '../flow/nodeBounds'

const DURATION = 1100
const SETTLE_MS = 40
const MAX_ZOOM = 0.95
const MIN_ZOOM = 0.34
const PADDING = 260
const MIN_SPAN_X = 1500
const MIN_SPAN_Y = 780

function padded(bounds) {
  const cx = (bounds.minX + bounds.maxX) / 2
  const cy = (bounds.minY + bounds.maxY) / 2
  const halfX = Math.max((bounds.maxX - bounds.minX) / 2, MIN_SPAN_X / 2)
  const halfY = Math.max((bounds.maxY - bounds.minY) / 2, MIN_SPAN_Y / 2)
  return { cx, cy, spanX: halfX * 2, spanY: halfY * 2 }
}

export default function TourCamera({ focusIds, tick, rightInset = 0 }) {
  const { getNode, setViewport } = useReactFlow()
  const width = useStore(s => s.width)
  const height = useStore(s => s.height)

  useEffect(() => {
    if (!width || !height) return undefined
    const frame = setTimeout(() => {
      const nodes = (focusIds ?? []).map(getNode).filter(Boolean)
      if (!nodes.length) return
      const usable = Math.max(240, width - rightInset)
      const { cx, cy, spanX, spanY } = padded(boundsOf(nodes))
      const zoom = Math.max(MIN_ZOOM, Math.min(
        MAX_ZOOM,
        Math.min(usable / (spanX + PADDING), height / (spanY + PADDING)),
      ))
      setViewport(
        { x: usable / 2 - cx * zoom, y: height / 2 - cy * zoom, zoom },
        { duration: DURATION },
      )
    }, SETTLE_MS)
    return () => clearTimeout(frame)
  }, [tick, focusIds, rightInset, getNode, setViewport, width, height])

  return null
}
