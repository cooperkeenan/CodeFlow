import { useEffect, useRef } from 'react'
import { useReactFlow, useStore } from 'reactflow'
import { GEOMETRY_FALLBACK } from './geometryFallback'
import { cssFrameProgress } from './cameraEasing'

const DURATION = 360
const ISOLATE_DURATION = 760
const FIT_OPTIONS = { padding: 0.25, duration: 360 }

function boundsOf(nodes) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const node of nodes) {
    const w = node.width ?? GEOMETRY_FALLBACK.rect.width
    const h = node.height ?? GEOMETRY_FALLBACK.rect.height
    minX = Math.min(minX, node.position.x)
    minY = Math.min(minY, node.position.y)
    maxX = Math.max(maxX, node.position.x + w)
    maxY = Math.max(maxY, node.position.y + h)
  }
  return { minX, minY, maxX, maxY }
}

function fitOffset(min, max, viewportSize, zoom, current) {
  const size = (max - min) * zoom
  if (size <= viewportSize) {
    const s0 = min * zoom + current
    const s1 = max * zoom + current
    if (s0 < 0) return current - s0
    if (s1 > viewportSize) return current + (viewportSize - s1)
    return current
  }
  return viewportSize / 2 - ((min + max) / 2) * zoom
}

function makeInterpolate(matchFrame) {
  return (a, b) => t => {
    const p = matchFrame.current ? cssFrameProgress(t) : t
    return [a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p, a[2] + (b[2] - a[2]) * p]
  }
}

export default function CameraController({ revealTrigger, isolateCenter = null }) {
  const { getNode, getViewport, setViewport, fitView } = useReactFlow()
  const width = useStore(s => s.width)
  const height = useStore(s => s.height)
  const d3Zoom = useStore(s => s.d3Zoom)
  const activeIsolateId = useRef(null)
  const matchFrame = useRef(false)

  useEffect(() => {
    if (d3Zoom) d3Zoom.interpolate(makeInterpolate(matchFrame))
  }, [d3Zoom])

  useEffect(() => {
    if (!revealTrigger) return
    if (revealTrigger.fit) {
      fitView(FIT_OPTIONS)
      return
    }
    const frame = requestAnimationFrame(() => {
      matchFrame.current = false
      const children = revealTrigger.childIds.map(getNode).filter(Boolean)
      const nodes = [getNode(revealTrigger.parentId), ...children].filter(Boolean)
      if (!nodes.length || !width || !height) return
      const { x, y, zoom } = getViewport()
      const b = boundsOf(nodes)
      setViewport(
        {
          x: fitOffset(b.minX, b.maxX, width, zoom, x),
          y: fitOffset(b.minY, b.maxY, height, zoom, y),
          zoom,
        },
        { duration: DURATION },
      )
    })
    return () => cancelAnimationFrame(frame)
  }, [revealTrigger, getNode, getViewport, setViewport, fitView, width, height])

  useEffect(() => {
    if (!isolateCenter || !width || !height) {
      activeIsolateId.current = null
      return
    }
    const key = `${isolateCenter.id}:${isolateCenter.phase}`
    if (activeIsolateId.current === key) return
    activeIsolateId.current = key
    matchFrame.current = true
    const { zoom } = getViewport()
    setViewport(
      {
        x: width / 2 - isolateCenter.cx * zoom,
        y: height / 2 - isolateCenter.cy * zoom,
        zoom,
      },
      { duration: ISOLATE_DURATION },
    )
  }, [isolateCenter, getViewport, setViewport, width, height])

  return null
}
