import { NODE_W, NODE_H, CY, HUB_GAP } from '../common'
import { gridTemplate } from './gridTemplate'

export function hubTemplate(members) {
  if (members.length < 2) return gridTemplate(members)
  const [hub, ...spokes] = members
  const spokesH = spokes.length * NODE_H + (spokes.length - 1) * CY
  const colX = NODE_W + HUB_GAP
  const placed = [{ name: hub.name, x: 0, y: Math.max(0, (spokesH - NODE_H) / 2) }]
  spokes.forEach((s, i) => placed.push({ name: s.name, x: colX, y: i * (NODE_H + CY) }))
  const edges = spokes.map(s => ({ source: hub.name, target: s.name }))
  return { width: colX + NODE_W, height: Math.max(NODE_H, spokesH), placed, edges }
}
