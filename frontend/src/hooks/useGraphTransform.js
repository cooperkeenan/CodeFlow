import { useMemo } from 'react'
import dagre from 'dagre'

const NODE_W = 190
const NODE_H = 64
const GROUP_PADDING = 24
const GROUP_HEADER = 28

function applyLayout(nodes, edges) {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: 60, ranksep: 80, marginx: 40, marginy: 40 })

  nodes.forEach(n => g.setNode(n.id, { width: NODE_W, height: NODE_H }))
  edges.forEach(e => {
    if (g.hasNode(e.source) && g.hasNode(e.target)) {
      g.setEdge(e.source, e.target)
    }
  })

  dagre.layout(g)

  return nodes.map(n => ({
    ...n,
    position: {
      x: g.node(n.id).x - NODE_W / 2,
      y: g.node(n.id).y - NODE_H / 2,
    },
  }))
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
  const allChildNames = new Set(components.flatMap(c => c.children ?? []))
  const topLevel = components.filter(c => !allChildNames.has(c.name))
  const topLevelNames = new Set(topLevel.map(c => c.name))
  const actorNames = new Set(spec.external_actors.map(a => a.name))
  const visibleNames = new Set([...topLevelNames, ...actorNames])

  const rawNodes = [
    ...topLevel.map(c => toRFNode(c.name, {
      label: c.name,
      layer: c.layer,
      isEntry: spec.entry_points.includes(c.name),
      drillable: (c.children?.length ?? 0) > 0,
      description: c.description,
      file_path: c.file_path,
      io: c.io,
    })),
    ...spec.external_actors.map(a => toRFNode(a.name, {
      label: a.name,
      layer: 'external',
      isEntry: false,
      drillable: false,
      description: a.description,
      actorType: a.type,
    })),
  ]

  const edges = spec.edges
    .filter(e => visibleNames.has(e.source) && visibleNames.has(e.target))
    .map(toRFEdge)

  const laidOut = applyLayout(rawNodes, edges)

  // Compute bounding box per layer
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

  // Group container nodes (rendered behind children)
  const groupNodes = Object.entries(bounds).map(([layer, b]) => ({
    id: `group_${layer}`,
    type: 'layerGroup',
    selectable: false,
    position: {
      x: b.minX - GROUP_PADDING,
      y: b.minY - GROUP_PADDING - GROUP_HEADER,
    },
    style: {
      width: b.maxX - b.minX + GROUP_PADDING * 2,
      height: b.maxY - b.minY + GROUP_PADDING * 2 + GROUP_HEADER,
      pointerEvents: 'none',
      zIndex: -1,
    },
    data: { layer },
  }))

  // Convert child positions to be relative to their group container
  const adjustedNodes = laidOut.map(node => {
    const layer = node.data.layer
    const b = bounds[layer]
    const groupX = b.minX - GROUP_PADDING
    const groupY = b.minY - GROUP_PADDING - GROUP_HEADER
    return {
      ...node,
      parentNode: `group_${layer}`,
      extent: 'parent',
      position: {
        x: node.position.x - groupX,
        y: node.position.y - groupY,
      },
    }
  })

  // Group nodes must appear before their children in the array
  return { nodes: [...groupNodes, ...adjustedNodes], edges }
}

// Expands single-child chains automatically when drilling down
function collectInvolved(rootName, componentMap) {
  const involved = new Set([rootName])
  const queue = [rootName]

  while (queue.length > 0) {
    const name = queue.shift()
    const children = componentMap[name]?.children ?? []
    for (const child of children) {
      involved.add(child)
    }
    if (children.length === 1) {
      queue.push(children[0])
    }
  }

  return involved
}

function buildComponentGraph(spec, componentName) {
  const componentMap = Object.fromEntries(
    flattenComponents(spec.layers).map(c => [c.name, c])
  )

  const root = componentMap[componentName]
  if (!root) return { nodes: [], edges: [] }

  const involved = collectInvolved(componentName, componentMap)

  const nodes = [...involved].map(name => {
    const c = componentMap[name]
    const isRoot = name === componentName
    return toRFNode(name, {
      label: name,
      layer: c?.layer ?? 'business',
      isEntry: isRoot,
      drillable: !isRoot && (c?.children?.length ?? 0) > 0,
      description: c?.description,
      file_path: c?.file_path,
      io: c?.io,
    })
  })

  const edges = spec.edges
    .filter(e => involved.has(e.source) && involved.has(e.target))
    .map(toRFEdge)

  return { nodes: applyLayout(nodes, edges), edges }
}

export function useGraphTransform(spec, focusComponent) {
  return useMemo(() => {
    if (!spec) return { nodes: [], edges: [] }
    return focusComponent
      ? buildComponentGraph(spec, focusComponent)
      : buildSystemGraph(spec)
  }, [spec, focusComponent])
}