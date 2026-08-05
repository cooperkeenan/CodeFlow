function isMember(node, id) {
  return (node?.data?.hiddenChildren ?? []).some(c => c.id === id)
}

function resolveHead(id, placed, expanded, seen = new Set()) {
  if (seen.has(id) || !expanded.has(id)) return id
  const head = placed.get(id)?.data?.bodyHead
  if (!head || !placed.has(head)) return id
  return resolveHead(head, placed, expanded, new Set(seen).add(id))
}

function resolveTails(id, placed, expanded, seen = new Set()) {
  if (seen.has(id) || !expanded.has(id)) return [id]
  const tails = placed.get(id)?.data?.bodyTails ?? []
  if (!tails.length) return [id]
  const nextSeen = new Set(seen).add(id)
  return tails.flatMap(tail => resolveTails(tail, placed, expanded, nextSeen))
}

export function routeChainEdges(edges, placed, expanded) {
  const routed = []
  for (const edge of edges) {
    const sourceNode = placed.get(edge.source)
    const targetNode = placed.get(edge.target)
    const fromBody = expanded.has(edge.source) && !isMember(sourceNode, edge.target)
    const intoBody = expanded.has(edge.target) && !isMember(targetNode, edge.source)
    const sources = fromBody ? resolveTails(edge.source, placed, expanded) : [edge.source]
    const target = intoBody ? resolveHead(edge.target, placed, expanded) : edge.target
    for (const source of sources) {
      if (source === target) continue
      routed.push({ ...edge, id: `${edge.id}::${source}->${target}`, source, target })
    }
  }
  return routed
}
