import { useMemo, useRef } from 'react'
import { useStore } from 'reactflow'
import { isolateRect, spreadNodes } from '../components/flow/isolateLayout'
import { useIsolateAnimation } from './useIsolateAnimation'

const DIM_MS = 160
const EXPAND_MS = 760
const SPREAD_MARGIN = 60

function edgeClass(edge, isolatedId) {
  if (isolatedId && edge.source !== isolatedId && edge.target !== isolatedId) return 'rf-dim'
  return undefined
}

function scaleFrom(node, rect) {
  const width = node.data.geometry?.width
  if (!rect?.width || !width) return 0.1
  return Math.round((width / rect.width) * 1000) / 1000
}

function closeScale(node, rect, frameScale) {
  const width = node.data.geometry?.width
  if (!rect?.width || !width) return frameScale
  return frameScale * (width / rect.width)
}

function frameData(node, highlighted, repo, geometry, frameScale, mode, ready, rect, growing, from, to) {
  return {
    ...node.data,
    highlighted: highlighted.has(node.id),
    ...(geometry ? { geometry } : {}),
    isolated: mode,
    dashed: true,
    repo,
    frameScale,
    frameReady: Boolean(ready),
    frameWidth: rect?.width ?? 0,
    frameHeight: rect?.height ?? 0,
    frameFrom: from,
    frameTo: to,
    frameGrowing: Boolean(growing),
  }
}

function otherNode(node, isolatedId, highlighted, offset, shift) {
  const dimmed = isolatedId || shift
  return {
    ...node,
    selected: false,
    className: [dimmed ? 'rf-dim' : '', shift ? 'rf-shift' : ''].filter(Boolean).join(' ') || undefined,
    position: offset
      ? { x: node.position.x + offset.dx, y: node.position.y + offset.dy }
      : node.position,
    data: { ...node.data, highlighted: highlighted.has(node.id) },
  }
}

export function useIsolatedView(nodes, edges, selectedId, isolatedId, hoveredEdge, repo) {
  const canvasW = useStore(s => s.width)
  const canvasH = useStore(s => s.height)
  const zoom = useStore(s => s.transform[2])
  const phase = useIsolateAnimation(isolatedId, DIM_MS, EXPAND_MS)
  const liveZoom = useRef(zoom)
  const frozenZoom = useRef(null)
  liveZoom.current = zoom
  const { grown, dashed, animating, swapped } = phase
  const closingId = isolatedId || swapped ? null : phase.id
  const restoringId = isolatedId ? null : swapped ? phase.id : null
  const frameScale = 1 / (frozenZoom.current || 1)
  const lastRect = useRef(null)

  const highlighted = useMemo(() => {
    const edge = edges.find(e => e.id === hoveredEdge)
    return edge ? new Set([edge.source, edge.target]) : new Set()
  }, [hoveredEdge, edges])

  const isolation = useMemo(() => {
    if (!isolatedId || !canvasW || !canvasH) {
      frozenZoom.current = null
      return null
    }
    const node = nodes.find(n => n.id === isolatedId)
    if (!node) return null
    if (frozenZoom.current === null) frozenZoom.current = liveZoom.current || 1
    const rect = isolateRect(node, canvasW, canvasH, frozenZoom.current)
    lastRect.current = rect
    return { rect, offsets: spreadNodes(nodes, rect, isolatedId, SPREAD_MARGIN) }
  }, [nodes, isolatedId, canvasW, canvasH])

  const rfNodes = useMemo(() => {
    if (closingId) {
      return nodes.map(n =>
        n.id === closingId
          ? { ...n, selected: true, zIndex: 8, className: 'rf-iso rf-shift', data: frameData(n, highlighted, repo, null, frameScale, 'closing', true, lastRect.current, true, 1, scaleFrom(n, lastRect.current)) }
          : otherNode(n, null, highlighted, null, true),
      )
    }
    if (restoringId) {
      return nodes.map(n =>
        n.id === restoringId
          ? {
              ...n,
              selected: false,
              zIndex: 8,
              className: 'rf-shift rf-swap-in',
              data: { ...n.data, highlighted: highlighted.has(n.id) },
            }
          : otherNode(n, null, highlighted, null, true),
      )
    }
    if (!isolation || !grown) {
      return nodes.map(n => ({
        ...n,
        selected: n.id === selectedId && n.id !== isolatedId,
        className: isolatedId && n.id !== isolatedId ? 'rf-dim' : undefined,
        data: { ...n.data, highlighted: highlighted.has(n.id) },
      }))
    }
    const { rect, offsets } = isolation
    return nodes.map(n =>
      n.id === isolatedId
        ? {
            ...n,
            selected: true,
            zIndex: 8,
            className: 'rf-iso',
            position: { x: rect.x, y: rect.y },
            data: {
              ...frameData(n, highlighted, repo, { width: rect.width, height: rect.height }, frameScale, 'open', !animating, rect, animating, scaleFrom(n, rect), 1),
              dashed: n.data.dashed || dashed,
            },
          }
        : otherNode(n, isolatedId, highlighted, offsets.get(n.id) ?? { dx: 0, dy: 0 }, true),
    )
  }, [nodes, selectedId, isolatedId, closingId, highlighted, isolation, grown, dashed, animating, repo, frameScale, restoringId])

  const rfEdges = useMemo(() => edges.map(e => ({
    ...e,
    className: edgeClass(e, isolatedId),
    data: { ...e.data, highlighted: e.id === hoveredEdge },
  })), [edges, hoveredEdge, isolatedId])

  const isolateCenter = isolation && isolatedId
    ? { id: isolatedId, cx: isolation.rect.cx, cy: isolation.rect.cy }
    : null

  return { rfNodes, rfEdges, isolateCenter }
}
