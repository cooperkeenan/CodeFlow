import { MarkerType } from 'reactflow'
import {
  NODE_W, NODE_H,
  colorForModule, flattenComponents, mapComponentToModule, toRFEdge,
} from './common'

const COL_GAP = 100
const ROW_GAP = 28

export function buildComponentGraph(spec, componentName) {
  const compToMod = mapComponentToModule(spec)
  const flat = flattenComponents(spec)
  const componentMap = new Map(flat.map(c => [c.name, c]))
  const focused = componentMap.get(componentName)
  if (!focused) return { nodes: [], edges: [] }

  const { callers, callees } = neighbours(spec.edges, componentName)
  const related = new Set([componentName, ...callers, ...callees])
  const children = (focused.children ?? []).filter(n => componentMap.has(n) && !related.has(n))
  const involved = new Set([...related, ...children])

  const colW = NODE_W + COL_GAP
  const rowH = NODE_H + ROW_GAP
  const callerH = Math.max(1, callers.length) * rowH
  const calleeH = Math.max(1, callees.length) * rowH
  const bandH = Math.max(callerH, calleeH, rowH)

  const nodes = [
    ...callers.map((name, i) =>
      columnNode(name, componentMap.get(name), spec, compToMod, {
        x: 0,
        y: (bandH - callerH) / 2 + i * rowH,
      })
    ),
    columnNode(componentName, focused, spec, compToMod, {
      x: colW,
      y: (bandH - rowH) / 2,
      isEntry: true,
      drillable: false,
    }),
    ...callees.map((name, i) =>
      columnNode(name, componentMap.get(name), spec, compToMod, {
        x: 2 * colW,
        y: (bandH - calleeH) / 2 + i * rowH,
      })
    ),
    ...children.map((name, i) =>
      columnNode(name, componentMap.get(name), spec, compToMod, {
        x: colW,
        y: bandH + ROW_GAP + i * rowH,
      })
    ),
  ]

  const edges = spec.edges
    .filter(e => e.edge_type !== 'import')
    .filter(e => involved.has(e.source) && involved.has(e.target) && e.source !== e.target)
    .map(e => toRFEdge(e))
    .concat(children.map(name => containsEdge(componentName, name)))

  return { nodes, edges }
}

function containsEdge(source, target) {
  const stroke = '#2a2a2a'
  return {
    id: `${source}~contains~${target}`,
    source,
    target,
    label: 'contains',
    type: 'smoothstep',
    animated: false,
    style: { stroke, strokeWidth: 1, strokeDasharray: '4 3' },
    markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: stroke },
    labelStyle: { fill: '#666', fontSize: 9, fontFamily: 'IBM Plex Mono, monospace' },
    labelBgStyle: { fill: '#0a0a0a', fillOpacity: 0.85 },
  }
}

function neighbours(edges, componentName) {
  const callerSet = new Set()
  const calleeSet = new Set()
  for (const e of edges) {
    if (e.source === e.target || e.edge_type === 'import') continue
    if (e.target === componentName) callerSet.add(e.source)
    if (e.source === componentName) calleeSet.add(e.target)
  }
  return { callers: [...callerSet].sort(), callees: [...calleeSet].sort() }
}

function columnNode(name, comp, spec, compToMod, layout) {
  const moduleName = compToMod.get(name)
  return {
    id: name,
    type: 'custom',
    position: { x: layout.x, y: layout.y },
    data: {
      label: name,
      module: moduleName,
      zone: comp?.zone,
      color: moduleName ? colorForModule(spec, moduleName) : undefined,
      isEntry: layout.isEntry ?? false,
      drillable: layout.drillable ?? (comp?.children?.length > 0),
      description: comp?.description,
      file_path: comp?.file_path,
      io: comp?.io,
    },
  }
}
