import { GEOMETRY_FALLBACK } from './geometryFallback'

const FILL = 0.92
const MIN_W = 520
const MIN_H = 340
const GROUP_TYPE = 'flowGroup'
const BOX_PREFIX = 'box:'

function boxOf(node) {
  if (node.type === GROUP_TYPE) {
    return { x: node.position.x, y: node.position.y, w: node.data.width, h: node.data.height }
  }
  const geometry = node.data.geometry ?? GEOMETRY_FALLBACK[node.data.shape] ?? GEOMETRY_FALLBACK.rect
  return { x: node.position.x, y: node.position.y, w: geometry.width, h: geometry.height }
}

export function isolateRect(node, canvasW, canvasH, zoom) {
  const box = boxOf(node)
  const width = Math.max(MIN_W, (canvasW * FILL) / zoom)
  const height = Math.max(MIN_H, (canvasH * FILL) / zoom)
  return {
    x: box.x,
    y: box.y,
    width: Math.round(width),
    height: Math.round(height),
    cx: box.x + width / 2,
    cy: box.y + height / 2,
  }
}

function sideOf(box, rect) {
  const nx = (box.x + box.w / 2 - rect.cx) / (rect.width / 2)
  const ny = (box.y + box.h / 2 - rect.cy) / (rect.height / 2)
  if (Math.abs(nx) >= Math.abs(ny)) return nx >= 0 ? 'right' : 'left'
  return ny >= 0 ? 'down' : 'up'
}

function clearanceOf(side, box, rect, margin) {
  if (side === 'right') return Math.max(0, rect.x + rect.width + margin - box.x)
  if (side === 'left') return Math.max(0, box.x + box.w - (rect.x - margin))
  if (side === 'down') return Math.max(0, rect.y + rect.height + margin - box.y)
  return Math.max(0, box.y + box.h - (rect.y - margin))
}

const AXIS = { left: 'x', right: 'x', up: 'y', down: 'y' }
const EXTENT = { x: 'w', y: 'h' }
const GAP = 48

function cascade(members, side, rect, margin, offsets) {
  const axis = AXIS[side]
  const size = EXTENT[axis]
  const forward = side === 'right' || side === 'down'
  const ordered = [...members].sort((a, b) =>
    forward ? a.box[axis] - b.box[axis] : b.box[axis] - a.box[axis],
  )
  let frontier = forward
    ? (axis === 'x' ? rect.x + rect.width : rect.y + rect.height) + margin
    : (axis === 'x' ? rect.x : rect.y) - margin
  for (const member of ordered) {
    const start = member.box[axis]
    const extent = member.box[size]
    const moved = forward
      ? Math.max(start, frontier)
      : Math.min(start + extent, frontier) - extent
    frontier = forward ? moved + extent + GAP : moved - GAP
    const delta = moved - start
    if (delta === 0) continue
    offsets.set(member.id, axis === 'x' ? { dx: delta, dy: 0 } : { dx: 0, dy: delta })
  }
}

export function spreadNodes(nodes, rect, isolatedId, margin) {
  const bySide = { left: [], right: [], up: [], down: [] }
  for (const node of nodes) {
    if (node.id === isolatedId || node.type === GROUP_TYPE) continue
    const box = boxOf(node)
    bySide[sideOf(box, rect)].push({ id: node.id, box })
  }

  const offsets = new Map()
  for (const side of ['left', 'right', 'up', 'down']) {
    if (bySide[side].some(m => clearanceOf(side, m.box, rect, margin) > 0)) {
      cascade(bySide[side], side, rect, margin, offsets)
    }
  }
  for (const node of nodes) {
    if (node.type !== GROUP_TYPE) continue
    const owner = offsets.get(node.id.slice(BOX_PREFIX.length))
    if (owner) offsets.set(node.id, owner)
  }
  return offsets
}
