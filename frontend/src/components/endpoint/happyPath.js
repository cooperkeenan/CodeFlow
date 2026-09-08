const ERROR_TEXT = /not found|error|raise|denied|invalid|fail|unauthor|forbidden|missing|40\d|50\d/i
const ERROR_ARMS = /except|error|invalid|missing|false|no\b/i

const ID_OWNER = /^[a-z]+:(.+):\d+$/

function ownerOf(node) {
  if (node.data?.ownerFqn) return node.data.ownerFqn
  const match = ID_OWNER.exec(node.id ?? '')
  return match ? match[1] : ''
}
const labelOf = node => `${node.data?.fullLabel ?? node.data?.label ?? ''} ${node.data?.oneLiner ?? ''}`

function isFailure(node, edge) {
  if (edge && ERROR_ARMS.test(edge.label ?? '')) return true
  if (edge?.data?.dashed) return true
  return node.data?.kind === 'outcome' && ERROR_TEXT.test(labelOf(node))
}

function rank(node, edge, handlerFqn) {
  return (
    (isFailure(node, edge) ? 0 : 4)
    + (ownerOf(node) === handlerFqn ? 2 : 0)
    + (edge.data?.isSpine || edge.isSpine ? 1 : 0)
  )
}

function shortestPath(fromId, targets, outgoing, byId) {
  const queue = [[fromId]]
  const seen = new Set([fromId])
  while (queue.length) {
    const path = queue.shift()
    const last = path[path.length - 1]
    if (targets.has(last) && path.length > 1) return path
    for (const edge of outgoing.get(last) ?? []) {
      if (seen.has(edge.target) || !byId.has(edge.target)) continue
      seen.add(edge.target)
      queue.push([...path, edge.target])
    }
  }
  return targets.has(fromId) ? [fromId] : null
}

export function happyPath(nodes, edges, handlerFqn) {
  if (!handlerFqn) return null
  const byId = new Map(nodes.map(n => [n.id, n]))
  const owned = new Set(nodes.filter(n => ownerOf(n) === handlerFqn).map(n => n.id))
  if (!owned.size) return null

  const outgoing = new Map()
  for (const edge of edges) {
    if (!byId.has(edge.source) || !byId.has(edge.target)) continue
    if (!outgoing.has(edge.source)) outgoing.set(edge.source, [])
    outgoing.get(edge.source).push(edge)
  }
  const incoming = new Set(edges.map(e => e.target))
  const root = nodes.find(n => n.data?.kind === 'entry' && !incoming.has(n.id)) ?? nodes[0]

  const prefix = shortestPath(root.id, owned, outgoing, byId) ?? [...owned].slice(0, 1)
  const walk = [...prefix]
  const visited = new Set(walk)
  for (;;) {
    const candidates = (outgoing.get(walk[walk.length - 1]) ?? [])
      .filter(edge => !visited.has(edge.target) && byId.has(edge.target))
    if (!candidates.length) break
    const best = candidates.reduce((a, b) =>
      rank(byId.get(b.target), b, handlerFqn) > rank(byId.get(a.target), a, handlerFqn) ? b : a)
    walk.push(best.target)
    visited.add(best.target)
  }

  const nodeIds = new Set(walk)
  const edgeIds = new Set(
    edges
      .filter(e => nodeIds.has(e.source) && nodeIds.has(e.target)
        && walk.indexOf(e.target) === walk.indexOf(e.source) + 1)
      .map(e => e.id)
  )
  return { nodeIds, edgeIds }
}
