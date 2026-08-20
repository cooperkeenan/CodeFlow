import { scaleGeometry } from '../components/flow/depthScale'
import { GEOMETRY_FALLBACK } from '../components/flow/geometryFallback'

const BOX_PAD = 30
const NESTED_GAP = 16

function fallbackFor(shape) {
  return GEOMETRY_FALLBACK[shape] ?? GEOMETRY_FALLBACK.rect
}

function union(rect, minX, minY, maxX, maxY) {
  return [
    Math.min(rect[0], minX),
    Math.min(rect[1], minY),
    Math.max(rect[2], maxX),
    Math.max(rect[3], maxY),
  ]
}

function rectOf(box, placed, geometry, inner) {
  const owner = placed.get(box.ownerId)
  const members = box.members.map(id => placed.get(id)).filter(Boolean)
  if (!owner || !members.length) return null
  let rect = [Infinity, Infinity, -Infinity, -Infinity]
  for (const node of [owner, ...members]) {
    const g = scaleGeometry(geometry?.[node.shape] ?? fallbackFor(node.shape), node.scale ?? 1)
    rect = union(rect, node.position.x, node.position.y, node.position.x + g.width, node.position.y + g.height)
    const nested = inner.get(node.id)
    if (nested) {
      const gap = Math.round(NESTED_GAP * box.scale)
      rect = union(rect, nested[0] - gap, nested[1] - gap, nested[2] + gap, nested[3] + gap)
    }
  }
  const pad = Math.round(BOX_PAD * box.scale)
  return [rect[0] - pad, rect[1] - pad, rect[2] + pad, rect[3] + pad]
}

const SIBLING_GUTTER = 96

function measureExtentX(nodes, geometry) {
  let minX = Infinity
  let maxX = -Infinity
  for (const node of nodes) {
    const g = scaleGeometry(geometry?.[node.shape] ?? fallbackFor(node.shape), node.scale ?? 1)
    minX = Math.min(minX, node.position.x)
    maxX = Math.max(maxX, node.position.x + g.width)
  }
  return [minX, maxX]
}

function shiftX(nodes, dx) {
  for (const node of nodes) {
    node.position = { x: node.position.x + dx, y: node.position.y }
  }
}

export function pushBelow(order, pivotY, amount) {
  for (const node of order) {
    if (node.position.y > pivotY) {
      node.position = { x: node.position.x, y: node.position.y + amount }
    }
  }
}

export function spaceSiblings(groups, geometry) {
  const rowMaxX = new Map()
  for (const group of groups) {
    const [minX, maxX] = measureExtentX(group.members, geometry)
    const row = Math.round(Math.min(...group.members.map(node => node.position.y)))
    const prevMaxX = rowMaxX.get(row)
    if (prevMaxX !== undefined) {
      const overflow = prevMaxX + SIBLING_GUTTER - minX
      if (overflow > 0) {
        shiftX(group.members, overflow)
        rowMaxX.set(row, maxX + overflow)
        continue
      }
    }
    rowMaxX.set(row, maxX)
  }
}

export function buildBoxes(boxes, placed, geometry) {
  const inner = new Map()
  const built = []
  for (const box of boxes) {
    const rect = rectOf(box, placed, geometry, inner)
    if (!rect) continue
    inner.set(box.ownerId, rect)
    built.push({
      id: `box:${box.ownerId}`,
      type: 'flowGroup',
      position: { x: rect[0], y: rect[1] },
      shape: 'group',
      label: '',
      data: {
        width: rect[2] - rect[0],
        height: rect[3] - rect[1],
        ownerKind: box.kind,
        scale: box.scale,
      },
    })
  }
  return built.reverse()
}
