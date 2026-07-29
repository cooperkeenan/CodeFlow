export const EMPTY_OVERLAY = {
  deleted_edge_ids: [],
  deleted_node_ids: [],
  added_edges: [],
  edge_overrides: {},
  node_overrides: {},
  text_nodes: [],
}

function withBase(existing) {
  return { ...EMPTY_OVERLAY, ...existing }
}

export function addEdgeReducer(overlay, edge) {
  const o = withBase(overlay)
  const already = o.added_edges.some(e => e.id === edge.id)
  if (already) return overlay
  return { ...o, added_edges: [...o.added_edges, edge] }
}

export function deleteElementsReducer(overlay, { nodeIds = [], edgeIds = [] }) {
  const o = withBase(overlay)
  const localNodeIds = new Set(o.text_nodes.map(n => n.id))
  const localEdgeIds = new Set(o.added_edges.map(e => e.id))

  const newTextNodes = o.text_nodes.filter(n => !nodeIds.includes(n.id))
  const newAddedEdges = o.added_edges.filter(e => !edgeIds.includes(e.id))

  const newDeletedNodeIds = [
    ...o.deleted_node_ids,
    ...nodeIds.filter(id => !localNodeIds.has(id) && !o.deleted_node_ids.includes(id)),
  ]
  const newDeletedEdgeIds = [
    ...o.deleted_edge_ids,
    ...edgeIds.filter(id => !localEdgeIds.has(id) && !o.deleted_edge_ids.includes(id)),
  ]

  return {
    ...o,
    deleted_node_ids: newDeletedNodeIds,
    deleted_edge_ids: newDeletedEdgeIds,
    text_nodes: newTextNodes,
    added_edges: newAddedEdges,
  }
}

export function setEdgeMarkerReducer(overlay, edgeId, markerEnd, markerStart) {
  const o = withBase(overlay)
  const prev = o.edge_overrides[edgeId] || {}
  const update = { ...prev, markerEnd }
  if (markerStart !== undefined) update.markerStart = markerStart
  return { ...o, edge_overrides: { ...o.edge_overrides, [edgeId]: update } }
}

export function setEdgeStyleReducer(overlay, edgeId, style) {
  const o = withBase(overlay)
  const prev = o.edge_overrides[edgeId] || {}
  return { ...o, edge_overrides: { ...o.edge_overrides, [edgeId]: { ...prev, style } } }
}

export function moveNodeReducer(overlay, nodeId, position) {
  const o = withBase(overlay)
  const prev = o.node_overrides[nodeId] || {}
  return { ...o, node_overrides: { ...o.node_overrides, [nodeId]: { ...prev, position } } }
}

export function setNodeLabelReducer(overlay, nodeId, label) {
  const o = withBase(overlay)
  const prev = o.node_overrides[nodeId] || {}
  return { ...o, node_overrides: { ...o.node_overrides, [nodeId]: { ...prev, label } } }
}

export function addTextNodeReducer(overlay, node) {
  const o = withBase(overlay)
  const already = o.text_nodes.some(n => n.id === node.id)
  if (already) return overlay
  return { ...o, text_nodes: [...o.text_nodes, node] }
}

export function setTextNodeLabelReducer(overlay, nodeId, text) {
  const o = withBase(overlay)
  const textNodes = o.text_nodes.map(n =>
    n.id === nodeId ? { ...n, data: { ...n.data, text } } : n
  )
  return { ...o, text_nodes: textNodes }
}

export function bumpTextFontReducer(overlay, nodeId, delta) {
  const o = withBase(overlay)
  const textNodes = o.text_nodes.map(n => {
    if (n.id !== nodeId) return n
    const next = Math.min(48, Math.max(8, (n.data.fontSize ?? 13) + delta))
    return { ...n, data: { ...n.data, fontSize: next } }
  })
  return { ...o, text_nodes: textNodes }
}

export function setTextColorReducer(overlay, nodeId, color) {
  const o = withBase(overlay)
  const textNodes = o.text_nodes.map(n =>
    n.id === nodeId ? { ...n, data: { ...n.data, color } } : n
  )
  return { ...o, text_nodes: textNodes }
}
