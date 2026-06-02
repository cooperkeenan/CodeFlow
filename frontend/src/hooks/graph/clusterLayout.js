import {
  NODE_W, NODE_H, CY, ZPADX, ZPADY, ZHEAD, ZGAP, MPAD, MHEAD,
  CPADX, CPADY, CHEAD, CGAP, CLUSTERS_PER_ROW, chunk,
} from './common'
import { resolveTemplate } from './templates/registry'

function clustersForZone(zone, comps, planByZone) {
  const base = planByZone.get(zone) ?? []
  const referenced = new Set()
  const walk = cs => cs.forEach(c => {
    (c.members ?? []).forEach(m => referenced.add(m))
    walk(c.children ?? [])
  })
  walk(base)
  const leftovers = comps.filter(c => !referenced.has(c.name) && !c.nested).map(c => c.name)
  const clusters = [...base]
  if (leftovers.length) {
    clusters.push({ label: clusters.length ? 'Other' : 'Components', style: 'grid', members: leftovers })
  }
  return clusters
}

function visibleMembers(cluster, byName, expandedZones, keyBase) {
  const all = (cluster.members ?? []).map(n => byName.get(n)).filter(Boolean)
  const primary = all.filter(c => c.tier !== 'secondary')
  const key = `${keyBase}::${cluster.label}`
  const expanded = expandedZones.has(key)
  return { shown: expanded ? all : primary, hidden: all.length - primary.length, key, expanded }
}

function layoutCluster(cluster, byName, expandedZones, keyBase) {
  const { shown, hidden, key, expanded } = visibleMembers(cluster, byName, expandedZones, keyBase)
  const children = (cluster.children ?? []).map(ch => layoutCluster(ch, byName, expandedZones, keyBase))
  const tpl = resolveTemplate(cluster.style)(shown)
  const parts = []
  if (shown.length) parts.push({ kind: 'tpl', w: tpl.width, h: tpl.height })
  for (const ch of children) parts.push({ kind: 'child', w: ch.boxW, h: ch.boxH, ref: ch })
  if (hidden > 0) parts.push({ kind: 'more', w: NODE_W, h: NODE_H })
  const innerW = Math.max(NODE_W, ...parts.map(p => p.w))
  const ox = CPADX
  const oy = CHEAD + CPADY
  const placed = []
  let more = null
  let y = oy
  for (const part of parts) {
    const px = ox + (innerW - part.w) / 2
    if (part.kind === 'tpl') tpl.placed.forEach(p => placed.push({ name: p.name, x: px + p.x, y: y + p.y }))
    else if (part.kind === 'child') { part.ref.relX = px; part.ref.relY = y }
    else more = { key, count: hidden, expanded, x: px, y }
    y += part.h + CY
  }
  const boxW = innerW + 2 * CPADX
  const boxH = (parts.length ? y - CY : oy) + CPADY
  const edges = [...tpl.edges, ...children.flatMap(c => c.edges)]
  return { label: cluster.label, boxW, boxH, placed, children, more, edges }
}

function layoutZone(clusters, byName, expandedZones, keyBase) {
  const descs = clusters.map(c => layoutCluster(c, byName, expandedZones, keyBase))
  const rows = chunk(descs, CLUSTERS_PER_ROW)
  let y = ZHEAD + ZPADY
  let contentW = 0
  for (const row of rows) {
    contentW = Math.max(contentW, row.reduce((s, d) => s + d.boxW, 0) + (row.length - 1) * CGAP)
    const rowH = Math.max(...row.map(d => d.boxH))
    let x = ZPADX
    for (const d of row) { d.relX = x; d.relY = y; x += d.boxW + CGAP }
    y += rowH + CGAP
  }
  return { descs, boxW: contentW + 2 * ZPADX, boxH: y - CGAP + ZPADY }
}

function emitCluster(desc, parentId, prefix, color, entry, zone, moduleName, acc) {
  const cid = `cluster__${prefix}__${desc.label}`
  acc.clusterNodes.push({
    id: cid, type: 'clusterGroup', selectable: false, draggable: false,
    parentNode: parentId, extent: 'parent',
    position: { x: desc.relX, y: desc.relY }, style: { width: desc.boxW, height: desc.boxH },
    data: { label: desc.label, color },
  })
  for (const { name, x, y } of desc.placed) {
    const c = acc.byName.get(name)
    acc.compNodes.push({
      id: name, type: 'custom', parentNode: cid, extent: 'parent', position: { x, y },
      data: {
        label: name, module: moduleName, zone, color, isEntry: entry.has(name),
        drillable: (c?.children?.length > 0), role: c.role, description: c.description, file_path: c.file_path, io: c.io,
      },
    })
  }
  for (const child of desc.children) emitCluster(child, cid, `${prefix}__${desc.label}`, color, entry, zone, moduleName, acc)
  if (desc.more) {
    acc.moreNodes.push({
      id: `more__${prefix}__${desc.label}`, type: 'zoneMore', draggable: false,
      parentNode: cid, extent: 'parent', position: { x: desc.more.x, y: desc.more.y },
      data: { key: desc.more.key, count: desc.more.count, expanded: desc.more.expanded, color },
    })
  }
}

export function buildClusteredModule(module, color, expandedZones, entry) {
  const byName = new Map()
  for (const comps of Object.values(module.zones)) for (const c of comps) byName.set(c.name, c)
  const planByZone = new Map((module.cluster_plan ?? []).map(p => [p.zone, p.clusters]))
  const acc = { clusterNodes: [], compNodes: [], moreNodes: [], byName }
  const zoneEntries = Object.entries(module.zones).filter(([, comps]) => comps.length)
  const orderEdges = []
  const zoneNodes = []
  let zy = MHEAD
  let innerW = 0
  const zoneBoxes = []
  for (const [zone, comps] of zoneEntries) {
    const clusters = clustersForZone(zone, comps, planByZone)
    const zl = layoutZone(clusters, byName, expandedZones, `${module.name}::${zone}`)
    zoneBoxes.push({ zone, zl, relY: zy })
    innerW = Math.max(innerW, zl.boxW)
    zy += zl.boxH + ZGAP
  }
  for (const { zone, zl, relY } of zoneBoxes) {
    const zid = `zone__${module.name}__${zone}`
    zoneNodes.push({
      id: zid, type: 'zoneGroup', selectable: false, draggable: false,
      parentNode: `mod__${module.name}`, extent: 'parent',
      position: { x: MPAD, y: relY }, style: { width: innerW, height: zl.boxH, zIndex: -1 },
      data: { label: zone, color },
    })
    for (const desc of zl.descs) {
      emitCluster(desc, zid, `${module.name}__${zone}`, color, entry, zone, module.name, acc)
      orderEdges.push(...desc.edges)
    }
  }
  const width = innerW + 2 * MPAD
  const height = zy - ZGAP + MPAD
  const moduleNode = {
    id: `mod__${module.name}`, type: 'moduleGroup', selectable: false, draggable: false,
    position: { x: 0, y: 0 }, style: { width, height, zIndex: -2 },
    data: { label: module.name, color },
  }
  const nodes = [moduleNode, ...zoneNodes, ...acc.clusterNodes, ...acc.compNodes, ...acc.moreNodes]
  return { nodes, width, orderEdges }
}
