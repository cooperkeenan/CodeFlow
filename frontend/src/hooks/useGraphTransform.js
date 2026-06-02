import { useMemo } from 'react'

import { buildSystemGraph } from './graph/systemGraph'
import { buildModuleGraph } from './graph/moduleGraph'
import { buildComponentGraph } from './graph/componentGraph'

export function useGraphTransform(spec, focus, expandedZones) {
  return useMemo(() => {
    if (!spec) return { nodes: [], edges: [] }
    if (!focus) return buildSystemGraph(spec)
    if (focus.kind === 'module') return buildModuleGraph(spec, focus.id, expandedZones)
    return buildComponentGraph(spec, focus.id)
  }, [spec, focus, expandedZones])
}
