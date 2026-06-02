import {
  NODE_W, NODE_H, CX, CY, ZPADX, ZPADY, ZHEAD, ZGAP, MPAD, MHEAD, PER_ROW, chunk,
} from './common'

function visibleCells(moduleName, zone, comps, expandedZones) {
  const key = `${moduleName}::${zone}`
  const isExpanded = expandedZones.has(key)
  const topLevel = comps.filter(c => !c.nested)
  const primary = topLevel.filter(c => c.tier !== 'secondary')
  const hidden = topLevel.length - primary.length
  const cells = (isExpanded ? topLevel : primary).map(c => ({ comp: c }))
  if (hidden > 0) cells.push({ more: true, key, count: hidden, expanded: isExpanded })
  return cells
}

function layoutModule(module, color, expandedZones) {
  const zones = Object.entries(module.zones).filter(([, comps]) => comps.length)
  const zoneLayouts = zones.map(([zone, comps]) => {
    const cells = visibleCells(module.name, zone, comps, expandedZones)
    const rows = chunk(cells, PER_ROW)
    const contentW = Math.max(...rows.map(r => r.length * NODE_W + (r.length - 1) * CX))
    const contentH = rows.length * NODE_H + (rows.length - 1) * CY
    return { zone, rows, contentW, contentH }
  }).filter(z => z.rows.length)
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
      for (const cell of row) {
        z.placed.push({ cell, x: cx, y: cy })
        cx += NODE_W + CX
      }
      cy += NODE_H + CY
    }
    zy += z.boxH + ZGAP
  }
  return { name: module.name, color, zoneLayouts, width: boxW + 2 * MPAD, height: zy - ZGAP + MPAD }
}

function emitModule(ml, entry) {
  const moduleNode = {
    id: `mod__${ml.name}`, type: 'moduleGroup', selectable: false, draggable: false,
    position: { x: 0, y: 0 }, style: { width: ml.width, height: ml.height, zIndex: -2 },
    data: { label: ml.name, color: ml.color },
  }
  const zoneNodes = []
  const compNodes = []
  const moreNodes = []
  for (const z of ml.zoneLayouts) {
    const zid = `zone__${ml.name}__${z.zone}`
    zoneNodes.push({
      id: zid, type: 'zoneGroup', selectable: false, draggable: false,
      parentNode: `mod__${ml.name}`, extent: 'parent',
      position: { x: z.relX, y: z.relY }, style: { width: z.boxW, height: z.boxH, zIndex: -1 },
      data: { label: z.zone, color: ml.color },
    })
    for (const { cell, x, y } of z.placed) {
      if (cell.more) {
        moreNodes.push({
          id: `more__${ml.name}__${z.zone}`, type: 'zoneMore', draggable: false,
          parentNode: zid, extent: 'parent', position: { x, y },
          data: { key: cell.key, count: cell.count, expanded: cell.expanded, color: ml.color },
        })
        continue
      }
      const c = cell.comp
      compNodes.push({
        id: c.name, type: 'custom', parentNode: zid, extent: 'parent', position: { x, y },
        data: {
          label: c.name, module: ml.name, zone: z.zone, color: ml.color,
          isEntry: entry.has(c.name), drillable: (c.children?.length > 0), role: c.role,
          description: c.description, file_path: c.file_path, io: c.io,
        },
      })
    }
  }
  return { moduleNode, zoneNodes, compNodes, moreNodes }
}

export function buildFlatModule(module, color, expandedZones, entry) {
  const ml = layoutModule(module, color, expandedZones)
  const { moduleNode, zoneNodes, compNodes, moreNodes } = emitModule(ml, entry)
  return {
    nodes: [moduleNode, ...zoneNodes, ...compNodes, ...moreNodes],
    width: ml.width,
    orderEdges: [],
  }
}
