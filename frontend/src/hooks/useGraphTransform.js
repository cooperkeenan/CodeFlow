import { useMemo } from 'react'
import dagre from 'dagre'

const NODE_W = 190
const NODE_H = 64

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

  const nodes = [
    ...components.map(c =>
      toRFNode(c.name, {
        label: c.name,
        layer: c.layer,
        isEntry: spec.entry_points.includes(c.name),
        drillable: (c.children?.length ?? 0) > 0,
        description: c.description,
        file_path: c.file_path,
        io: c.io,
      })
    ),
    ...spec.external_actors.map(a =>
      toRFNode(a.name, {
        label: a.name,
        layer: 'external',
        isEntry: false,
        drillable: false,
        description: a.description,
        actorType: a.type,
      })
    ),
  ]

  const edges = spec.edges.map(toRFEdge)

  return { nodes: applyLayout(nodes, edges), edges }
}

function buildComponentGraph(spec, componentName) {
  const componentMap = Object.fromEntries(
    flattenComponents(spec.layers).map(c => [c.name, c])
  )

  const root = componentMap[componentName]
  if (!root) return { nodes: [], edges: [] }

  const childNames = new Set(root.children ?? [])
  const involved = new Set([componentName, ...childNames])

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