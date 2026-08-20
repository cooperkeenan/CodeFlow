import { GEOMETRY_FALLBACK } from './geometryFallback'

export function boundsOf(nodes) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const node of nodes) {
    const w = node.width ?? GEOMETRY_FALLBACK.rect.width
    const h = node.height ?? GEOMETRY_FALLBACK.rect.height
    minX = Math.min(minX, node.position.x)
    minY = Math.min(minY, node.position.y)
    maxX = Math.max(maxX, node.position.x + w)
    maxY = Math.max(maxY, node.position.y + h)
  }
  return { minX, minY, maxX, maxY }
}
