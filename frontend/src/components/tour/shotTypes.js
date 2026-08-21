export const MIN_ZOOM = 0.34

export const DEFAULT_SHOT = 'medium'

export const SOLO_SPAN = { x: 820, y: 520 }

export const SHOTS = {
  detail: { maxZoom: 1.6, pad: 200, duration: 900 },
  medium: { maxZoom: 1.15, pad: 240, duration: 1100 },
  wide: { maxZoom: 0.95, pad: 280, duration: 1300 },
  establish: { maxZoom: 0.5, pad: 400, duration: 1500 },
  card: { maxZoom: 1.0, pad: 260, duration: 800 },
}

export function shotFor(name) {
  return SHOTS[name] || SHOTS[DEFAULT_SHOT]
}

export function zoomFor(shot, span, usable) {
  const raw = Math.min(usable.width / (span.x + shot.pad), usable.height / (span.y + shot.pad))
  return Math.max(MIN_ZOOM, Math.min(shot.maxZoom, raw))
}
