import { useMemo } from 'react'

import { colorForModule, toRFEdge } from './graph/common'

export function useGraphTransform(spec, focus, expandedZones, views) {
  return useMemo(() => {
    if (!views) return { nodes: [], edges: [] }
    const viewId = !focus ? 'system'
      : focus.kind === 'module' ? `module:${focus.id}`
      : `component:${focus.id}`
    const view = views[viewId]
    if (!view) return { nodes: [], edges: [] }

    const nodes = view.nodes.map(n => {
      const moduleName = n.data?.module ?? n.data?.moduleName
      const color = moduleName ? colorForModule(spec, moduleName) : undefined
      const data = { ...n.data, ...(color ? { color } : {}) }
      if (n.type === 'zoneMore') data.expanded = expandedZones.has(n.data?.key ?? '')
      return { ...n, data }
    })

    const edges = view.edges.map(e => toRFEdge(e, { id: e.id, label: e.label }))
    return { nodes, edges }
  }, [spec, focus, expandedZones, views])
}
