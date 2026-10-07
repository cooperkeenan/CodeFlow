import { useMemo } from 'react'

export function useHappyHighlight(baseNodes, baseEdges, happy) {
  const nodeIds = useMemo(() => (happy ? new Set(happy.node_ids) : null), [happy])
  const edgeKeys = useMemo(
    () => (happy ? new Set(happy.edges.map(([s, t]) => `${s}\u0000${t}`)) : null), [happy]
  )
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
    if (!edgeKeys) return baseEdges
    return baseEdges.map(e => {
      const on = edgeKeys.has(`${e.source}\u0000${e.target}`)
      return { ...e, className: on ? 'rf-happy' : e.className, data: { ...e.data, happy: on, muted: !on } }
    })
  }, [baseEdges, edgeKeys])
  const fitNodeIds = useMemo(() => (happy ? [...happy.node_ids] : null), [happy])
  return { nodes, edges, fitNodeIds }
}
