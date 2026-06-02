import { MODULE_PALETTE } from '../../constants'

import {
  NODE_H, MOD_W, MOD_H,
  mapComponentToModule, externalActorNode, toRFEdge, dedupeRawEdges,
} from './common'
import { buildFlatModule } from './flatLayout'
import { buildClusteredModule } from './clusterLayout'

const GHOST_GAP = 80

export function buildModuleGraph(spec, moduleName, expandedZones) {
  const idx = spec.modules.findIndex(m => m.name === moduleName)
  if (idx < 0) return { nodes: [], edges: [] }
  const color = MODULE_PALETTE[idx % MODULE_PALETTE.length]
  const expanded = expandedZones ?? new Set()
  const module = spec.modules[idx]
  const entry = new Set(spec.entry_points)
  const built = (module.cluster_plan?.length)
    ? buildClusteredModule(module, color, expanded, entry)
    : buildFlatModule(module, color, expanded, entry)

  const compToMod = mapComponentToModule(spec)
  const neighbours = collectNeighbours(spec, moduleName, compToMod)
  const neighbourNodes = layoutGhosts(neighbours, spec.modules, built.width + GHOST_GAP)

  const actorX = built.width + GHOST_GAP + (neighbourNodes.length ? MOD_W + GHOST_GAP : 0)
  const actorNodes = spec.external_actors.map((a, i) => externalActorNode(a, actorX, i * (NODE_H + 24)))

  const componentIds = new Set(built.nodes.filter(n => n.type === 'custom').map(n => n.id))
  const ghostIds = new Set(neighbourNodes.map(n => n.id))
  const actorIds = new Set(actorNodes.map(n => n.id))
  const edges = buildModuleEdges(spec.edges, moduleName, compToMod, componentIds, ghostIds, actorIds)
  appendOrderEdges(edges, built.orderEdges, componentIds)

  return {
    nodes: [...built.nodes, ...neighbourNodes, ...actorNodes],
    edges,
  }
}

function collectNeighbours(spec, moduleName, compToMod) {
  const neighbours = new Set()
  for (const e of spec.edges) {
    const src = compToMod.get(e.source)
    const tgt = compToMod.get(e.target)
    if (!src || !tgt || src === tgt) continue
    if (src === moduleName && tgt !== moduleName) neighbours.add(tgt)
    if (tgt === moduleName && src !== moduleName) neighbours.add(src)
  }
  return [...neighbours].sort()
}

function layoutGhosts(neighbours, modules, x) {
  return neighbours.map((name, i) => {
    const idx = modules.findIndex(m => m.name === name)
    return {
      id: `ghost__${name}`,
      type: 'moduleGhost',
      position: { x, y: i * (MOD_H + 20) },
      data: { label: name, color: MODULE_PALETTE[(idx < 0 ? 0 : idx) % MODULE_PALETTE.length] },
    }
  })
}

function buildModuleEdges(edges, moduleName, compToMod, componentIds, ghostIds, actorIds) {
  const remapped = []
  for (const e of edges) {
    if (e.edge_type === 'import') continue
    const srcMod = compToMod.get(e.source)
    const tgtMod = compToMod.get(e.target)
    let source = null
    let target = null
    if (srcMod === moduleName && componentIds.has(e.source)) source = e.source
    if (tgtMod === moduleName && componentIds.has(e.target)) target = e.target
    else if (tgtMod && tgtMod !== moduleName && ghostIds.has(`ghost__${tgtMod}`)) target = `ghost__${tgtMod}`
    else if (actorIds.has(e.target)) target = e.target
    if (!source || !target) continue
    remapped.push({ source, target, edge_type: e.edge_type, primary: e.primary })
  }
  const validIds = new Set([...componentIds, ...ghostIds, ...actorIds])
  return dedupeRawEdges(remapped, validIds).map(e => toRFEdge(e))
}

function appendOrderEdges(edges, orderEdges, componentIds) {
  const seen = new Set(edges.map(e => `${e.source}->${e.target}`))
  for (const e of orderEdges) {
    const key = `${e.source}->${e.target}`
    if (seen.has(key) || !componentIds.has(e.source) || !componentIds.has(e.target)) continue
    seen.add(key)
    edges.push(toRFEdge({ source: e.source, target: e.target, edge_type: 'call', primary: true }, { id: `order__${key}` }))
  }
}
