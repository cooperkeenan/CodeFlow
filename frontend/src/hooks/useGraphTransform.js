import { useMemo } from 'react'

import { colorForModule, toRFEdge } from './graph/common'

export function useGraphTransform(spec, focus, expandedZones, expandedNodes, views) {
  return useMemo(() => {
    if (!views) return { nodes: [], edges: [] }
    const viewId = !focus ? 'system'
      : focus.kind === 'module' ? `module:${focus.id}`
      : `component:${focus.id}`
    const view = views[viewId]
    if (!view) return { nodes: [], edges: [] }

    const isPipeline = view.type === 'pipeline'
    const HORIZONTAL = new Set(['pipeline', 'relationship', 'mesh', 'dependency_graph', 'layered_tier'])
    const isFlow = view.type === 'pipeline' || (focus?.kind === 'component' && HORIZONTAL.has(view.type))

    const nodes = view.nodes.map(n => {
      const moduleName = n.data?.module ?? n.data?.moduleName
      const color = moduleName ? colorForModule(spec, moduleName) : undefined
      const data = { ...n.data, ...(color ? { color } : {}) }
      data.expanded = n.type === 'zoneMore' ? expandedZones.has(n.data?.key ?? '') : expandedNodes.has(n.id)
      return { ...n, data, ...(isFlow ? { sourcePosition: 'right', targetPosition: 'left' } : {}) }
    })

    const edges = view.edges.map(e => ({
      ...toRFEdge(e, { id: e.id, label: e.label }),
      ...(isFlow ? { sourceHandle: 'right', targetHandle: 'left' } : {}),
    }))
    return { nodes, edges }
  }, [spec, focus, expandedZones, expandedNodes, views])
}
