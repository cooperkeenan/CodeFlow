import { useMemo } from 'react'
import { scaleGeometry } from '../components/flow/depthScale'

const HEADER_TYPE = 'laneHeader'
const GROUP_TYPE = 'flowGroup'

function toNode(node, onToggle, geometry) {
  const type =
    node.type === HEADER_TYPE || node.type === GROUP_TYPE
      ? node.type
      : node.shape === 'pipeline' ? 'pipeline' : node.kind
  const scale = node.scale ?? 1
  return {
    id: node.id,
    type,
    position: node.position,
    draggable: false,
    selectable: type !== HEADER_TYPE && type !== GROUP_TYPE,
    ...(type === GROUP_TYPE ? { zIndex: 0, focusable: false } : {}),
    data: {
      ...node.data,
      kind: node.kind,
      shape: node.shape,
      label: node.label,
      nodeId: node.id,
      geometry: scaleGeometry(geometry?.[node.shape], scale),
      scale,
      onToggle,
    },
    ...(type === HEADER_TYPE || type === GROUP_TYPE
      ? {}
      : { sourcePosition: 'bottom', targetPosition: 'top' }),
  }
}

function toEdge(edge) {
  return {
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: 'flow',
    label: edge.label || undefined,
    data: {
      kind: edge.kind,
      isSpine: !!edge.isSpine,
      dashed: !!edge.dashed,
      routed: edge.routed,
      confidence: edge.confidence,
      secondary: !!edge.secondary,
      scale: edge.scale ?? 1,
    },
  }
}

export function useGraphTransform(view, onToggle, geometry) {
  return useMemo(() => {
    if (!view?.nodes) return { nodes: [], edges: [] }
    return {
      nodes: view.nodes.map(node => toNode(node, onToggle, geometry)),
      edges: (view.edges ?? []).map(toEdge),
    }
  }, [view, onToggle, geometry])
}
