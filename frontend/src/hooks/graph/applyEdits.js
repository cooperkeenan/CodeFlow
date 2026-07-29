const EMPTY_OVERLAY = {
  deleted_edge_ids: [],
  deleted_node_ids: [],
  added_edges: [],
  edge_overrides: {},
  node_overrides: {},
  text_nodes: [],
}

function isEmptyOverlay(overlay) {
  if (!overlay) return true
  const o = overlay
  return (
    (!o.deleted_edge_ids || o.deleted_edge_ids.length === 0) &&
    (!o.deleted_node_ids || o.deleted_node_ids.length === 0) &&
    (!o.added_edges || o.added_edges.length === 0) &&
    (!o.edge_overrides || Object.keys(o.edge_overrides).length === 0) &&
    (!o.node_overrides || Object.keys(o.node_overrides).length === 0) &&
    (!o.text_nodes || o.text_nodes.length === 0)
  )
}

export function applyEdits(baseNodes, baseEdges, overlay) {
  if (isEmptyOverlay(overlay)) return { nodes: baseNodes, edges: baseEdges }

  const o = { ...EMPTY_OVERLAY, ...overlay }
  const deletedNodeIds = new Set(o.deleted_node_ids)
  const deletedEdgeIds = new Set(o.deleted_edge_ids)

  const nodes = baseNodes
    .filter(n => !deletedNodeIds.has(n.id))
    .map(n => {
      const overr = o.node_overrides[n.id]
      if (!overr) return n
      const updated = { ...n }
      if (overr.label !== undefined) updated.data = { ...n.data, label: overr.label }
      if (overr.position !== undefined) updated.position = overr.position
      return updated
    })

  const baseEdgeIds = new Set(baseEdges.map(e => e.id))

  const edges = baseEdges
    .filter(e => !deletedEdgeIds.has(e.id))
    .map(e => {
      const overr = o.edge_overrides[e.id]
      if (!overr) return e
      const merged = { ...e }
      if (overr.markerEnd !== undefined) merged.markerEnd = overr.markerEnd
      if (overr.markerStart !== undefined) merged.markerStart = overr.markerStart
      if (overr.style !== undefined) merged.style = { ...e.style, ...overr.style }
      if (overr.label !== undefined) merged.label = overr.label
      return merged
    })

  for (const ae of o.added_edges) {
    if (!baseEdgeIds.has(ae.id)) edges.push(ae)
  }

  for (const tn of o.text_nodes) {
    if (deletedNodeIds.has(tn.id)) continue
    const overr = o.node_overrides[tn.id]
    const resolved = overr?.position ? { ...tn, position: overr.position } : tn
    nodes.push(resolved)
  }

  return { nodes, edges }
}
