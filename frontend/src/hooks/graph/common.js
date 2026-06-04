import { MarkerType } from 'reactflow'
import { MODULE_PALETTE, EXTERNAL_COLOR } from '../../constants'

export const NODE_W = 180
export const NODE_H = 58
export const CX = 24
export const CY = 20
export const ZPADX = 14
export const ZPADY = 12
export const ZHEAD = 22
export const ZGAP = 14
export const MPAD = 16
export const MHEAD = 32
export const PER_ROW = 3

export const CPADX = 12
export const CPADY = 10
export const CHEAD = 20
export const CGAP = 22
export const CLUSTERS_PER_ROW = 3
export const HUB_GAP = 90

export const MOD_W = 240
export const MOD_H = 110
export const MOD_GAP_X = 110
export const MOD_GAP_Y = 130

export function chunk(arr, size) {
  const out = []
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size))
  return out
}

export function flattenComponents(spec) {
  return spec.modules.flatMap(m =>
    Object.entries(m.zones).flatMap(([zone, comps]) =>
      comps.map(c => ({ ...c, module: m.name, zone }))
    )
  )
}

export function mapComponentToModule(spec) {
  const map = new Map()
  for (const m of spec.modules) {
    for (const comps of Object.values(m.zones ?? {})) {
      for (const c of comps) map.set(c.name, m.name)
    }
  }
  return map
}

export function colorForModule(spec, moduleName) {
  const i = spec.modules.findIndex(m => m.name === moduleName)
  return MODULE_PALETTE[(i < 0 ? 0 : i) % MODULE_PALETTE.length]
}

export function moduleSummary(spec) {
  return spec.modules.map((m, i) => ({
    name: m.name,
    color: MODULE_PALETTE[i % MODULE_PALETTE.length],
    zoneCount: Object.entries(m.zones ?? {}).filter(([, c]) => c.length).length,
    componentCount: Object.values(m.zones ?? {}).reduce((s, comps) => s + comps.length, 0),
  }))
}

export function externalActorNode(actor, x, y) {
  return {
    id: actor.name, type: 'custom', position: { x, y },
    data: {
      label: actor.name, module: 'external', zone: actor.type, color: EXTERNAL_COLOR,
      isEntry: false, drillable: false, actorType: actor.type, description: actor.description,
    },
  }
}

export function toRFEdge(e, options = {}) {
  const animated = e.edge_type === 'http' || e.edge_type === 'event'
  const dim = e.primary === false
  const stroke = dim ? '#242424' : '#333333'
  return {
    id: options.id ?? `${e.source}->${e.target}`,
    source: e.source,
    target: e.target,
    label: options.label ?? (e.edge_type !== 'call' ? e.edge_type : undefined),
    type: 'smoothstep',
    animated: animated && !dim,
    style: dim
      ? { stroke, strokeWidth: 1, strokeDasharray: '3 3' }
      : { stroke, strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: stroke },
    labelStyle: { fill: 'rgba(255,255,255,0.38)', fontSize: 9, fontFamily: 'IBM Plex Mono, monospace' },
    labelBgStyle: { fill: '#121212', fillOpacity: 0.85 },
  }
}

export function dedupeRawEdges(rawEdges, validIds) {
  const seen = new Set()
  return rawEdges.filter(e => {
    if (e.source === e.target) return false
    if (!validIds.has(e.source) || !validIds.has(e.target)) return false
    const k = `${e.source}->${e.target}`
    if (seen.has(k)) return false
    seen.add(k)
    return true
  })
}
