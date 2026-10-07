import { useMemo } from 'react'

const rootOf = edge => edge.id.split('::')[0]

function happyEdgeIds(baseEdges, pairs) {
  const claimed = new Set()
  for (const [source, target] of pairs) {
    const free = e => !claimed.has(e.id)
    const match = baseEdges.find(e => free(e) && e.source === source && e.target === target)
      ?? baseEdges.find(e => free(e) && rootOf(e).startsWith(`${source}->${target}:`))
    if (match) claimed.add(match.id)
  }
  return claimed
}

export function useHappyHighlight(baseNodes, baseEdges, happy) {
  const nodeIds = useMemo(() => (happy ? new Set(happy.node_ids) : null), [happy])
  const nodes = useMemo(() => {
    if (!nodeIds) return baseNodes
    const className = happy.ends_in_failure ? 'rf-happy rf-happy-failure' : 'rf-happy'
    return baseNodes.map(n => (
      nodeIds.has(n.id)
        ? { ...n, className }
        : { ...n, data: { ...n.data, dimmed: n.type !== 'flowGroup' } }
    ))
  }, [baseNodes, nodeIds, happy])
  const edges = useMemo(() => {
    if (!happy) return baseEdges
    const on = happyEdgeIds(baseEdges, happy.edges)
    return baseEdges.map(e => {
      const hit = on.has(e.id)
      return { ...e, className: hit ? 'rf-happy' : e.className, data: { ...e.data, happy: hit, muted: !hit } }
    })
  }, [baseEdges, happy])
  const fitNodeIds = useMemo(() => (happy ? [...happy.node_ids] : null), [happy])
  return { nodes, edges, fitNodeIds }
}
