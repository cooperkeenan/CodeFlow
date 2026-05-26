import { useMemo } from 'react'
import dagre from 'dagre'

const NODE_W = 190
const NODE_H = 64
const NODE_X_GAP = 60
const LAYER_Y_GAP = 100
const GROUP_PADDING = 24
const GROUP_HEADER = 28
const EXTERNAL_X_OFFSET = 160

const LAYER_ORDER = ['presentation', 'business', 'data']
const DRILL_DOWN_THRESHOLD = 3

function applyDagreLayout(nodes, edges) {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: 60, ranksep: 80, marginx: 40, marginy: 40 })
  nodes.forEach(n => g.setNode(n.id, { width: NODE_W, height: NODE_H }))
  edges.forEach(e => {
    if (g.hasNode(e.source) && g.hasNode(e.target)) g.setEdge(e.source, e.target)
  })
  dagre.layout(g)
  return nodes.map(n => ({
    ...n,
    position: { x: g.node(n.id).x - NODE_W / 2, y: g.node(n.id).y - NODE_H / 2 },
  }))
}

// Custom layout for system view — stacks layers vertically, external to the right
function applySystemLayout(rawNodes) {
  const byLayer = {}
  const externalNodes = []

  for (const node of rawNodes) {
    const layer = node.data.layer
    if (layer === 'external') {
      externalNodes.push(node)
    } else {
      if (!byLayer[layer]) byLayer[layer] = []
      byLayer[layer].push(node)
    }
  }

  const layerWidths = LAYER_ORDER.map(l => {
    const count = (byLayer[l] ?? []).length
    return count > 0 ? count * NODE_W + (count - 1) * NODE_X_GAP : 0
  })
  const maxLayerWidth = Math.max(...layerWidths, 0)

  const positioned = []
  let currentY = 0

  for (const layer of LAYER_ORDER) {
    const layerNodes = byLayer[layer] ?? []
    if (layerNodes.length === 0) continue
    const layerWidth = layerNodes.length * NODE_W + (layerNodes.length - 1) * NODE_X_GAP
    let x = (maxLayerWidth - layerWidth) / 2
    for (const node of layerNodes) {
      positioned.push({ ...node, position: { x, y: currentY } })
      x += NODE_W + NODE_X_GAP
    }
    currentY += NODE_H + LAYER_Y_GAP
  }

  // Place external nodes to the right, vertically centred on the main content
  const mainHeight = currentY - LAYER_Y_GAP
  const externalTotalHeight = externalNodes.length * NODE_H + (externalNodes.length - 1) * 40
  const externalX = maxLayerWidth + EXTERNAL_X_OFFSET
  let ey = (mainHeight - externalTotalHeight) / 2

  for (const node of externalNodes) {
    positioned.push({ ...node, position: { x: externalX, y: ey } })
    ey += NODE_H + 40
  }

  return positioned
}

function buildGroups(laidOut) {
  const bounds = {}
  for (const node of laidOut) {
    const layer = node.data.layer
    if (!bounds[layer]) bounds[layer] = { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity }
    const b = bounds[layer]
    b.minX = Math.min(b.minX, node.position.x)
    b.minY = Math.min(b.minY, node.position.y)
    b.maxX = Math.max(b.maxX, node.position.x + NODE_W)
    b.maxY = Math.max(b.maxY, node.position.y + NODE_H)
  }

  const groupNodes = Object.entries(bounds).map(([layer, b]) => ({
    id: `group_${layer}`,
    type: 'layerGroup',
    selectable: false,
    position: { x: b.minX - GROUP_PADDING, y: b.minY - GROUP_PADDING - GROUP_HEADER },
    style: {
      width: b.maxX - b.minX + GROUP_PADDING * 2,
      height: b.maxY - b.minY + GROUP_PADDING * 2 + GROUP_HEADER,
      pointerEvents: 'none',
      zIndex: -1,
    },
    data: { layer },
  }))

  const adjustedNodes = laidOut.map(node => {
    const layer = node.data.layer
    const b = bounds[layer]
    const groupX = b.minX - GROUP_PADDING
    const groupY = b.minY - GROUP_PADDING - GROUP_HEADER
    return {
      ...node,
      parentNode: `group_${layer}`,
      extent: 'parent',
      position: { x: node.position.x - groupX, y: node.position.y - groupY },
    }
  })

  return { groupNodes, adjustedNodes }
}

function toRFEdge(e) {
  const isAnimated = e.edge_type === 'http' || e.edge_type === 'event'
  const showLabel = e.edge_type !== 'call'
  return {
    id: `${e.source}→${e.target}`,
    source: e.source,
    target: e.target,
    label: showLabel ? e.edge_type : undefined,
    type: 'smoothstep',
    animated: isAnimated,
    style: { stroke: '#2a2a2a', strokeWidth: 1.5 },
    labelStyle: { fill: '#555', fontSize: 9, fontFamily: 'IBM Plex Mono, monospace' },
    labelBgStyle: { fill: '#0a0a0a', fillOpacity: 0.8 },
  }
}

function toRFNode(id, data) {
  return { id, type: 'custom', data, position: { x: 0, y: 0 } }
}

function flattenComponents(layers) {
  return Object.entries(layers).flatMap(([layer, components]) =>
    components.map(c => ({ ...c, layer }))
  )
}

function buildSystemGraph(spec) {
  const components = flattenComponents(spec.layers)
  const componentMap = Object.fromEntries(components.map(c => [c.name, c]))

  // Roots: not a child of any other component
  const allChildNames = new Set(components.flatMap(c => c.children ?? []))
  const rootComponents = components.filter(c => !allChildNames.has(c.name))

  // BFS expansion: add component to visible set.
  // If it has < DRILL_DOWN_THRESHOLD children, also inline-expand those children.
  // If it has >= DRILL_DOWN_THRESHOLD children, it is collapsed (drill-down only).
  const visibleNames = new Set()
  const collapsedNames = new Set()

  function expand(name) {
    if (visibleNames.has(name)) return
    visibleNames.add(name)
    const c = componentMap[name]
    if (!c) return
    if ((c.children ?? []).length >= DRILL_DOWN_THRESHOLD) {
      collapsedNames.add(name)
    } else {
      for (const child of c.children ?? []) expand(child)
    }
  }

  for (const root of rootComponents) expand(root.name)

  // Parent map — used to reroute edges that target hidden children up to their
  // collapsed visible ancestor.
  const parentOf = {}
  for (const c of components) {
    for (const child of c.children ?? []) parentOf[child] = c.name
  }

  function resolveVisible(name) {
    let cur = name
    while (cur && !visibleNames.has(cur)) cur = parentOf[cur]
    return cur ?? name
  }

  const actorNames = new Set(spec.external_actors.map(a => a.name))
  const allVisible = new Set([...visibleNames, ...actorNames])

  const nodes = [
    ...components
      .filter(c => visibleNames.has(c.name))
      .map(c => toRFNode(c.name, {
        label: c.name, layer: c.layer,
        isEntry: spec.entry_points.includes(c.name),
        drillable: collapsedNames.has(c.name),
        description: c.description, file_path: c.file_path, io: c.io,
      })),
    ...spec.external_actors.map(a => toRFNode(a.name, {
      label: a.name, layer: 'external',
      isEntry: false, drillable: false,
      description: a.description, actorType: a.type,
    })),
  ]

  const seenEdgeKeys = new Set()
  const edges = spec.edges
    .map(e => ({ ...e, source: resolveVisible(e.source), target: resolveVisible(e.target) }))
    .filter(e => {
      if (e.source === e.target) return false
      if (!allVisible.has(e.source) || !allVisible.has(e.target)) return false
      const key = `${e.source}→${e.target}`
      if (seenEdgeKeys.has(key)) return false
      seenEdgeKeys.add(key)
      return true
    })
    .map(toRFEdge)

  const laidOut = applySystemLayout(nodes)
  const { groupNodes, adjustedNodes } = buildGroups(laidOut)
  return { nodes: [...groupNodes, ...adjustedNodes], edges }
}

function buildComponentGraph(spec, componentName) {
  const componentMap = Object.fromEntries(
    flattenComponents(spec.layers).map(c => [c.name, c])
  )
  const root = componentMap[componentName]
  if (!root) return { nodes: [], edges: [] }

  // A child that also appears in another sibling's children list is a grandchild —
  // exclude it so it only appears when the user drills into the intermediate parent.
  const directChildren = root.children ?? []
  const grandchildren = new Set(
    directChildren.flatMap(name => componentMap[name]?.children ?? [])
  )
  const trueDirectChildren = directChildren.filter(name => !grandchildren.has(name))
  const involved = new Set([componentName, ...trueDirectChildren])
  const nodes = [...involved].map(name => {
    const c = componentMap[name]
    const isRoot = name === componentName
    return toRFNode(name, {
      label: name, layer: c?.layer ?? 'business',
      isEntry: isRoot,
      drillable: !isRoot && (c?.children?.length ?? 0) > 0,
      description: c?.description, file_path: c?.file_path, io: c?.io,
    })
  })
  const edges = spec.edges
    .filter(e => involved.has(e.source) && involved.has(e.target))
    .map(toRFEdge)

  return { nodes: applyDagreLayout(nodes, edges), edges }
}

export function useGraphTransform(spec, focusComponent) {
  return useMemo(() => {
    if (!spec) return { nodes: [], edges: [] }
    return focusComponent
      ? buildComponentGraph(spec, focusComponent)
      : buildSystemGraph(spec)
  }, [spec, focusComponent])
}