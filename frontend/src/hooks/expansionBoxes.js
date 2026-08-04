import { scaleGeometry } from '../components/flow/depthScale'

const BOX_PAD = 26
const FALLBACK_GEOMETRY = { width: 200, height: 60 }

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
    const g = scaleGeometry(geometry?.[node.shape] ?? FALLBACK_GEOMETRY, node.scale ?? 1)
    rect = union(rect, node.position.x, node.position.y, node.position.x + g.width, node.position.y + g.height)
    const nested = inner.get(node.id)
    if (nested) rect = union(rect, nested[0], nested[1], nested[2], nested[3])
  }
  const pad = Math.round(BOX_PAD * box.scale)
  return [rect[0] - pad, rect[1] - pad, rect[2] + pad, rect[3] + pad]
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
