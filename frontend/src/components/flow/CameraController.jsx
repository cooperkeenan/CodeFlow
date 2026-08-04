import { useEffect, useRef } from 'react'
import { useReactFlow, useStore } from 'reactflow'
import { scaleOf } from './depthScale'

const DURATION = 360
const MAX_ZOOM = 2.6
const FIT_OPTIONS = { padding: 0.25, duration: 360 }

function boundsOf(nodes) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const node of nodes) {
    const w = node.width ?? 200
    const h = node.height ?? 60
    minX = Math.min(minX, node.position.x)
    minY = Math.min(minY, node.position.y)
    maxX = Math.max(maxX, node.position.x + w)
    maxY = Math.max(maxY, node.position.y + h)
  }
  return { minX, minY, maxX, maxY }
}

export default function CameraController({ revealTrigger }) {
  const { getNode, getViewport, setViewport, fitView } = useReactFlow()
  const width = useStore(s => s.width)
  const height = useStore(s => s.height)
  const baseZoom = useRef(null)

  useEffect(() => {
    if (!revealTrigger) return
    if (revealTrigger.fit) {
      baseZoom.current = null
      fitView(FIT_OPTIONS)
      return
    }
    const frame = requestAnimationFrame(() => {
      const children = revealTrigger.childIds.map(getNode).filter(Boolean)
      const nodes = [getNode(revealTrigger.parentId), ...children].filter(Boolean)
      if (!nodes.length || !width || !height) return
      const childScale = children[0]?.data?.scale ?? 1
      const current = getViewport().zoom
      if (childScale >= scaleOf(1) - 1e-6 || baseZoom.current === null) {
        baseZoom.current = current
      }
      const zoom = Math.min(MAX_ZOOM, baseZoom.current / childScale)
      const b = boundsOf(nodes)
      setViewport(
        {
          x: width / 2 - ((b.minX + b.maxX) / 2) * zoom,
          y: height / 2 - ((b.minY + b.maxY) / 2) * zoom,
          zoom,
        },
        { duration: DURATION },
      )
    })
    return () => cancelAnimationFrame(frame)
  }, [revealTrigger, getNode, getViewport, setViewport, fitView, width, height])

  return null
}
