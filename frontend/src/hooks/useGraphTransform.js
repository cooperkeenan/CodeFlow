import { useMemo } from 'react'

const HEADER_TYPE = 'laneHeader'

function toNode(node) {
  const type = node.type === HEADER_TYPE ? HEADER_TYPE : node.kind
  return {
    id: node.id,
    type,
    position: node.position,
    draggable: false,
    selectable: type !== HEADER_TYPE,
    data: { ...node.data, kind: node.kind, shape: node.shape, label: node.label },
    ...(type === HEADER_TYPE ? {} : { sourcePosition: 'right', targetPosition: 'left' }),
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
    },
  }
}

export function useGraphTransform(view) {
  return useMemo(() => {
    if (!view?.nodes) return { nodes: [], edges: [] }
    return {
      nodes: view.nodes.map(toNode),
      edges: (view.edges ?? []).map(toEdge),
    }
  }, [view])
}
