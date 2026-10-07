import { GEOMETRY_FALLBACK } from './geometryFallback'

const GROUP_TYPE = 'flowGroup'
const SPINE_GAP = 40
const SIDE_CLEARANCE = 96
const SETTLE_GAP = 48
const MAX_PASSES = 400

function sizeOf(node) {
  const g = node.data?.geometry ?? GEOMETRY_FALLBACK[node.data?.shape] ?? GEOMETRY_FALLBACK.rect
  return { w: g.width, h: g.height }
}

function overlaps(a, b) {
  return a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h
}

function byPosition(a, b) {
  return a.y - b.y || a.x - b.x || (a.id < b.id ? -1 : 1)
}

function placeSpine(path, cx) {
  const boxes = []
  let y = path[0].position.y
  for (const node of path) {
    const { w, h } = sizeOf(node)
    boxes.push({ id: node.id, x: cx - w / 2, y, w, h })
    y += h + SPINE_GAP
  }
  return boxes
}

function shiftSides(others, spine, cx) {
  const half = Math.max(...spine.map(b => b.w)) / 2
  const mean = spine.reduce((sum, b) => sum + b.x + b.w / 2, 0) / spine.length
  const left = others.filter(b => b.x + b.w / 2 < mean)
  const right = others.filter(b => b.x + b.w / 2 >= mean)
  const dxLeft = left.length
    ? Math.min(0, cx - half - SIDE_CLEARANCE - Math.max(...left.map(b => b.x + b.w)))
    : 0
  const dxRight = right.length
    ? Math.max(0, cx + half + SIDE_CLEARANCE - Math.min(...right.map(b => b.x)))
    : 0
  return [
    ...left.map(b => ({ ...b, x: b.x + dxLeft })),
    ...right.map(b => ({ ...b, x: b.x + dxRight })),
  ]
}

function settle(others, spine) {
  const placed = [...spine]
  const out = []
  for (const box of [...others].sort(byPosition)) {
    let current = box
    for (let pass = 0; pass < MAX_PASSES; pass += 1) {
      const hit = placed.find(p => overlaps(
        { ...current, x: current.x - 8, w: current.w + 16, y: current.y - 8, h: current.h + 16 }, p,
      ))
      if (!hit) break
      current = { ...current, y: hit.y + hit.h + SETTLE_GAP }
    }
    placed.push(current)
    out.push(current)
  }
  return out
}

function atFullScale(node, geometry) {
  const full = geometry?.[node.data?.shape]
  if (!full) return node
  return { ...node, data: { ...node.data, scale: 1, geometry: full } }
}

export function spineLayout(rawNodes, pathIds, geometry = null) {
  const onSpine = new Set(pathIds)
  const nodes = rawNodes.map(n => (onSpine.has(n.id) ? atFullScale(n, geometry) : n))
  const byId = new Map(nodes.map(n => [n.id, n]))
  const path = pathIds.map(id => byId.get(id)).filter(Boolean)
  if (path.length < 2) return nodes
  const { w: entryW } = sizeOf(path[0])
  const cx = path[0].position.x + entryW / 2
  const spine = placeSpine(path, cx)
  const onPath = new Set(path.map(n => n.id))
  const others = nodes
    .filter(n => !onPath.has(n.id) && n.type !== GROUP_TYPE)
    .map(n => ({ id: n.id, ...n.position, ...sizeOf(n) }))
  const moved = new Map([...spine, ...settle(shiftSides(others, spine, cx), spine)].map(b => [b.id, b]))
  return nodes
    .filter(n => n.type !== GROUP_TYPE)
    .map(n => ({ ...n, position: { x: moved.get(n.id).x, y: moved.get(n.id).y } }))
}
