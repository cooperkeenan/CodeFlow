import dagre from 'dagre'

import {
  MOD_W, MOD_H, MOD_GAP_X, MOD_GAP_Y,
  mapComponentToModule, moduleSummary, toRFEdge,
} from './common'

export function buildSystemGraph(spec) {
  const modules = moduleSummary(spec)
  const archetype = spec.layout_hint?.archetype ?? 'mesh'
  const order = spec.layout_hint?.module_order?.length
    ? spec.layout_hint.module_order
    : modules.map(m => m.name)
  const ranks = ranksFromHint(spec.layout_hint, modules.map(m => m.name))
  const positions = positionModules(archetype, modules, order, ranks)

  const compToMod = mapComponentToModule(spec)
  const validModules = new Set(modules.map(m => m.name))
  const aggregated = aggregateModuleEdges(spec.edges, compToMod, validModules)

  const nodes = modules.map(m => ({
    id: `mod__${m.name}`,
    type: 'moduleSummary',
    position: positions.get(m.name) ?? { x: 0, y: 0 },
    data: {
      label: m.name, color: m.color, drillable: true,
      moduleName: m.name, zoneCount: m.zoneCount, componentCount: m.componentCount,
    },
  }))

  const edges = [...aggregated.entries()].map(([key, value]) => {
    const [src, tgt] = key.split('->')
    return toModuleEdge(src, tgt, value)
  })
  return { nodes, edges }
}

function positionModules(archetype, modules, order, ranks) {
  if (archetype === 'pipeline') return positionPipeline(order)
  if (archetype === 'hub') return positionHub(order)
  if (archetype === 'layered' || archetype === 'hierarchy') return positionByRank(order, ranks)
  return positionMesh(modules)
}

function positionPipeline(order) {
  const map = new Map()
  order.forEach((name, i) => {
    map.set(name, { x: i * (MOD_W + MOD_GAP_X), y: 0 })
  })
  return map
}

function positionHub(order) {
  const map = new Map()
  if (!order.length) return map
  const [hub, ...spokes] = order
  const radius = Math.max(260, spokes.length * 65)
  map.set(hub, { x: 0, y: 0 })
  const n = spokes.length || 1
  spokes.forEach((name, i) => {
    const angle = (i / n) * 2 * Math.PI - Math.PI / 2
    map.set(name, {
      x: Math.round(Math.cos(angle) * radius),
      y: Math.round(Math.sin(angle) * radius),
    })
  })
  return map
}

function positionByRank(order, ranks) {
  const byRank = new Map()
  for (const name of order) {
    const r = ranks.get(name) ?? 0
    if (!byRank.has(r)) byRank.set(r, [])
    byRank.get(r).push(name)
  }
  const map = new Map()
  const sortedRanks = [...byRank.keys()].sort((a, b) => a - b)
  sortedRanks.forEach((rank, rowIdx) => {
    const row = byRank.get(rank)
    const rowW = row.length * MOD_W + (row.length - 1) * MOD_GAP_X
    row.forEach((name, i) => {
      map.set(name, {
        x: i * (MOD_W + MOD_GAP_X) - rowW / 2 + MOD_W / 2,
        y: rowIdx * (MOD_H + MOD_GAP_Y),
      })
    })
  })
  return map
}

function positionMesh(modules) {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: MOD_GAP_X, ranksep: MOD_GAP_Y, marginx: 40, marginy: 40 })
  modules.forEach(m => g.setNode(m.name, { width: MOD_W, height: MOD_H }))
  dagre.layout(g)
  const map = new Map()
  modules.forEach(m => {
    const n = g.node(m.name)
    map.set(m.name, { x: n.x - MOD_W / 2, y: n.y - MOD_H / 2 })
  })
  return map
}

function ranksFromHint(hint, fallback) {
  const map = new Map()
  if (hint?.rank_assignments) {
    for (const r of hint.rank_assignments) map.set(r.module_name, r.rank)
  } else {
    fallback.forEach(name => map.set(name, 0))
  }
  return map
}

function aggregateModuleEdges(edges, compToMod, validModules) {
  const agg = new Map()
  for (const e of edges) {
    const srcMod = compToMod.get(e.source)
    const tgtMod = compToMod.get(e.target)
    if (!srcMod || !tgtMod || srcMod === tgtMod) continue
    if (!validModules.has(srcMod) || !validModules.has(tgtMod)) continue
    const key = `${srcMod}->${tgtMod}`
    if (!agg.has(key)) agg.set(key, { types: {}, count: 0 })
    const a = agg.get(key)
    a.types[e.edge_type] = (a.types[e.edge_type] ?? 0) + 1
    a.count += 1
  }
  return agg
}

function toModuleEdge(srcMod, tgtMod, value) {
  const sortedTypes = Object.entries(value.types).sort((a, b) => b[1] - a[1])
  const dominant = sortedTypes[0]?.[0] ?? 'call'
  const label = value.count > 1 ? `${dominant} ×${value.count}` : dominant
  return toRFEdge(
    { source: `mod__${srcMod}`, target: `mod__${tgtMod}`, edge_type: dominant },
    { id: `mod__${srcMod}->mod__${tgtMod}`, label },
  )
}
