import { NODE_W, NODE_H, CY } from '../common'
import { gridTemplate } from './gridTemplate'

const VGAP = CY * 2

export function hierarchyTemplate(members) {
  if (members.length < 2) return gridTemplate(members)
  const [root, ...children] = members
  const block = gridTemplate(children)
  const width = Math.max(NODE_W, block.width)
  const yOff = NODE_H + VGAP
  const xOff = (width - block.width) / 2
  const placed = [{ name: root.name, x: (width - NODE_W) / 2, y: 0 }]
  for (const p of block.placed) placed.push({ name: p.name, x: p.x + xOff, y: p.y + yOff })
  const edges = children.map(c => ({ source: root.name, target: c.name }))
  return { width, height: yOff + block.height, placed, edges }
}
