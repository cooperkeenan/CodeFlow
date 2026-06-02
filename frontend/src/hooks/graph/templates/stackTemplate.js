import { NODE_W, NODE_H, CY } from '../common'

export function stackTemplate(members) {
  const placed = members.map((m, i) => ({ name: m.name, x: 0, y: i * (NODE_H + CY) }))
  const height = members.length ? members.length * NODE_H + (members.length - 1) * CY : 0
  return { width: NODE_W, height, placed, edges: [] }
}
