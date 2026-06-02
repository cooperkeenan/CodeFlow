import { NODE_W, NODE_H, CX, CY, PER_ROW, chunk } from '../common'

export function gridTemplate(members) {
  const rows = chunk(members, PER_ROW)
  const contentW = Math.max(NODE_W, ...rows.map(r => r.length * NODE_W + (r.length - 1) * CX))
  const placed = []
  let y = 0
  for (const row of rows) {
    const rowW = row.length * NODE_W + (row.length - 1) * CX
    let x = (contentW - rowW) / 2
    for (const m of row) {
      placed.push({ name: m.name, x, y })
      x += NODE_W + CX
    }
    y += NODE_H + CY
  }
  const height = rows.length ? rows.length * NODE_H + (rows.length - 1) * CY : 0
  return { width: contentW, height, placed, edges: [] }
}
