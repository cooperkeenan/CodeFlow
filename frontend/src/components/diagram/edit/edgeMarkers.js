import { MarkerType } from 'reactflow'

const DEFAULT_W = 16
const DEFAULT_H = 16

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

export function markerForArrowhead(kind) {
  if (kind === 'none') return null
  const stroke = cssVar('--edge')
  if (kind === 'open') return { type: MarkerType.Arrow, width: DEFAULT_W, height: DEFAULT_H, color: stroke }
  return { type: MarkerType.ArrowClosed, width: DEFAULT_W, height: DEFAULT_H, color: stroke }
}

export function styleForLineStyle(kind) {
  return kind === 'dashed' ? { strokeDasharray: '6 3' } : { strokeDasharray: undefined }
}

export function buildNewEdge(params) {
  const { source, target, sourceHandle, targetHandle } = params
  const stroke = cssVar('--edge')
  return {
    id: `e-${source}-${target}-${Date.now()}`,
    source,
    target,
    sourceHandle: sourceHandle ?? null,
    targetHandle: targetHandle ?? null,
    type: 'smoothstep',
    markerEnd: { type: MarkerType.ArrowClosed, width: DEFAULT_W, height: DEFAULT_H, color: stroke },
    style: { stroke, strokeWidth: 2 },
  }
}
