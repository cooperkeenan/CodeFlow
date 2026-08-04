export const DEPTH_SCALE = 0.76
export const MIN_SCALE = 0.42

export function scaleOf(depth) {
  const raw = DEPTH_SCALE ** Math.max(depth, 0)
  return Math.max(MIN_SCALE, Math.round(raw * 1000) / 1000)
}

export function scaleGeometry(geometry, scale = 1) {
  if (!geometry || scale === 1) return geometry
  return {
    width: Math.round(geometry.width * scale),
    height: Math.round(geometry.height * scale),
  }
}
