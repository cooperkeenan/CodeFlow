import { useMemo } from 'react'
import dagre from 'dagre'
import { MODULE_PALETTE, EXTERNAL_COLOR } from '../constants'

const NODE_W = 180
const NODE_H = 58
const CX = 24
const CY = 20
const ZPADX = 14
const ZPADY = 12
const ZHEAD = 22
const ZGAP = 14
const MPAD = 16
const MHEAD = 32
const MGAP = 44
const PER_ROW = 3
const DRILL_DOWN_THRESHOLD = 3

function chunk(arr, size) {
  const out = []
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size))
  return out
}

function flattenComponents(spec) {
  return spec.modules.flatMap(m =>
    Object.entries(m.zones).flatMap(([zone, comps]) =>
      comps.map(c => ({ ...c, module: m.name, zone }))
    )
  )
}

function colorForModule(spec, moduleName) {
  const i = spec.modules.findIndex(m => m.name === moduleName)
  return MODULE_PALETTE[(i < 0 ? 0 : i) % MODULE_PALETTE.length]
}

function isDrillable(comp) {
  return (comp.children?.length ?? 0) >= DRILL_DOWN_THRESHOLD
}

function layoutModule(module, color) {
  const zones = Object.entries(module.zones).filter(([, comps]) => comps.length)
  const zoneLayouts = zones.map(([zone, comps]) => {
    const rows = chunk(comps, PER_ROW)
    const contentW = Math.max(...rows.map(r => r.length * NODE_W + (r.length - 1) * CX))
    const contentH = rows.length * NODE_H + (rows.length - 1) * CY
    return { zone, rows, contentW, contentH }
  })
  const innerW = Math.max(0, ...zoneLayouts.map(z => z.contentW))
  const boxW = innerW + 2 * ZPADX

  let zy = MHEAD
  for (const z of zoneLayouts) {
    z.boxW = boxW
    z.boxH = ZHEAD + ZPADY + z.contentH + ZPADY
    z.relX = MPAD
    z.relY = zy
    z.placed = []
    let cy = ZHEAD + ZPADY
    for (const row of z.rows) {
      const rowW = row.length * NODE_W + (row.length - 1) * CX
      let cx = ZPADX + (innerW - rowW) / 2
      for (const c of row) {
        z.placed.push({ c, x: cx, y: cy })
        cx += NODE_W + CX
      }
      cy += NODE_H + CY
    }
    zy += z.boxH + ZGAP
  }

  return { name: module.name, color, zoneLayouts, width: boxW + 2 * MPAD, height: zy - ZGAP + MPAD }
}

function packModules(layouts) {
  const cols = Math.max(1, Math.ceil(Math.sqrt(layouts.length)))
  let y = 0
  let maxRight = 0
  for (const row of chunk(layouts, cols)) {
    let x = 0
    let rowH = 0
    for (const ml of row) {
      ml.absX = x
      ml.absY = y
      x += ml.width + MGAP
      rowH = Math.max(rowH, ml.height)
    }
    maxRight = Math.max(maxRight, x - MGAP)
    y += rowH + MGAP
  }
  return { maxRight }
}

function emitModule(ml, entry) {
  const moduleNode = {
    id: `mod__${ml.name}`, type: 'moduleGroup', selectable: false, draggable: false,
    position: { x: ml.absX, y: ml.absY }, style: { width: ml.width, height: ml.height, zIndex: -2 },
    data: { label: ml.name, color: ml.color },
  }
  const zoneNodes = []
  const compNodes = []
  for (const z of ml.zoneLayouts) {
    const zid = `zone__${ml.name}__${z.zone}`
    zoneNodes.push({
      id: zid, type: 'zoneGroup', selectable: false, draggable: false,
      parentNode: `mod__${ml.name}`, extent: 'parent',
      position: { x: z.relX, y: z.relY }, style: { width: z.boxW, height: z.boxH, zIndex: -1 },
      data: { label: z.zone, color: ml.color },
    })
    for (const { c, x, y } of z.placed) {
      compNodes.push({
        id: c.name, type: 'custom', parentNode: zid, extent: 'parent', position: { x, y },
        data: {
          label: c.name, module: ml.name, zone: z.zone, color: ml.color,
          isEntry: entry.has(c.name), drillable: isDrillable(c),
          description: c.description, file_path: c.file_path, io: c.io,
        },
      })
    }
  }
  return { moduleNode, zoneNodes, compNodes }
}

function actorNode(actor, x, y) {
  return {
    id: actor.name, type: 'custom', position: { x, y },
    data: {
      label: actor.name, module: 'external', zone: actor.type, color: EXTERNAL_COLOR,
      isEntry: false, drillable: false, actorType: actor.type, description: actor.description,
    },
  }
}

function toRFEdge(e) {
  const animated = e.edge_type === 'http' || e.edge_type === 'event'
  return {
    id: `${e.source}->${e.target}`,
    source: e.source,
    target: e.target,
    label: e.edge_type !== 'call' ? e.edge_type : undefined,
    type: 'smoothstep',
    animated,
    style: { stroke: '#2a2a2a', strokeWidth: 1.5 },
    labelStyle: { fill: '#555', fontSize: 9, fontFamily: 'IBM Plex Mono, monospace' },
    labelBgStyle: { fill: '#0a0a0a', fillOpacity: 0.8 },
  }
}

function buildEdges(rawEdges, nodeIds) {
  const seen = new Set()
  return rawEdges.filter(e => {
    if (e.source === e.target) return false
    if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) return false
    const k = `${e.source}->${e.target}`
    if (seen.has(k)) return false
    seen.add(k)
    return true
  }).map(toRFEdge)
}

function buildSystemGraph(spec) {
  const layouts = spec.modules.map((m, i) => layoutModule(m, MODULE_PALETTE[i % MODULE_PALETTE.length]))
  const { maxRight } = packModules(layouts)
  const entry = new Set(spec.entry_points)

  const moduleNodes = []
  const zoneNodes = []
  const compNodes = []
  for (const ml of layouts) {
    const e = emitModule(ml, entry)
    moduleNodes.push(e.moduleNode)
    zoneNodes.push(...e.zoneNodes)
    compNodes.push(...e.compNodes)
  }
  const actorNodes = spec.external_actors.map((a, i) => actorNode(a, maxRight + MGAP, i * (NODE_H + 24)))
  const ids = new Set([...compNodes, ...actorNodes].map(n => n.id))
  return { nodes: [...moduleNodes, ...zoneNodes, ...compNodes, ...actorNodes], edges: buildEdges(spec.edges, ids) }
}

function buildModuleGraph(spec, moduleName) {
  const idx = spec.modules.findIndex(m => m.name === moduleName)
  if (idx < 0) return { nodes: [], edges: [] }
  const ml = layoutModule(spec.modules[idx], MODULE_PALETTE[idx % MODULE_PALETTE.length])
  ml.absX = 0
  ml.absY = 0
  const { moduleNode, zoneNodes, compNodes } = emitModule(ml, new Set(spec.entry_points))
  const compIds = new Set(compNodes.map(n => n.id))
  const actorNodes = spec.external_actors.map((a, i) => actorNode(a, ml.width + MGAP, i * (NODE_H + 24)))
  const ids = new Set([...compIds, ...actorNodes.map(n => n.id)])
  const edges = buildEdges(spec.edges.filter(e => compIds.has(e.source) && ids.has(e.target)), ids)
  return { nodes: [moduleNode, ...zoneNodes, ...compNodes, ...actorNodes], edges }
}

function applyDagreLayout(nodes, edges) {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: 60, ranksep: 80, marginx: 40, marginy: 40 })
  nodes.forEach(n => g.setNode(n.id, { width: NODE_W, height: NODE_H }))
  edges.forEach(e => { if (g.hasNode(e.source) && g.hasNode(e.target)) g.setEdge(e.source, e.target) })
  dagre.layout(g)
  return nodes.map(n => ({ ...n, position: { x: g.node(n.id).x - NODE_W / 2, y: g.node(n.id).y - NODE_H / 2 } }))
}

function buildComponentGraph(spec, componentName) {
  const map = Object.fromEntries(flattenComponents(spec).map(c => [c.name, c]))
  const root = map[componentName]
  if (!root) return { nodes: [], edges: [] }
  const involved = new Set([componentName, ...(root.children ?? [])])
  const nodes = [...involved].map(name => {
    const c = map[name]
    return {
      id: name, type: 'custom', position: { x: 0, y: 0 },
      data: {
        label: name, module: c?.module, zone: c?.zone,
        color: c ? colorForModule(spec, c.module) : MODULE_PALETTE[0],
        isEntry: name === componentName,
        drillable: name !== componentName && c ? isDrillable(c) : false,
        description: c?.description, file_path: c?.file_path, io: c?.io,
      },
    }
  })
  const edges = buildEdges(spec.edges.filter(e => involved.has(e.source) && involved.has(e.target)), involved)
  return { nodes: applyDagreLayout(nodes, edges), edges }
}

export function useGraphTransform(spec, focus) {
  return useMemo(() => {
    if (!spec) return { nodes: [], edges: [] }
    if (!focus) return buildSystemGraph(spec)
    if (focus.kind === 'module') return buildModuleGraph(spec, focus.id)
    return buildComponentGraph(spec, focus.id)
  }, [spec, focus])
}
