import { KIND_ACCENT, SURFACE_2, TEXT_MUTED } from '../styles'

function tint(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

export const FLOWCHART_KIND_STYLE = {
  start: { fill: tint(KIND_ACCENT.entry, 0.16), stroke: KIND_ACCENT.entry, shape: 'pill' },
  end: { fill: tint(KIND_ACCENT.entry, 0.16), stroke: KIND_ACCENT.entry, shape: 'pill' },
  call: { fill: tint(KIND_ACCENT.step, 0.16), stroke: KIND_ACCENT.step, shape: 'rect' },
  effect: { fill: tint(KIND_ACCENT.effect, 0.16), stroke: KIND_ACCENT.effect, shape: 'rect' },
  decision: { fill: tint(KIND_ACCENT.decision, 0.16), stroke: KIND_ACCENT.decision, shape: 'diamond' },
  loop: { fill: tint(KIND_ACCENT.parallel, 0.16), stroke: KIND_ACCENT.parallel, shape: 'rect' },
  return: { fill: tint(KIND_ACCENT.outcome, 0.16), stroke: KIND_ACCENT.outcome, shape: 'pill' },
  raise: { fill: tint(KIND_ACCENT.outcome, 0.16), stroke: KIND_ACCENT.outcome, shape: 'pill' },
  more: { fill: 'transparent', stroke: TEXT_MUTED, shape: 'rect' },
}

const FALLBACK_STYLE = { fill: SURFACE_2, stroke: TEXT_MUTED, shape: 'rect' }

export function shapeFor(kind) {
  return FLOWCHART_KIND_STYLE[kind]?.shape ?? FALLBACK_STYLE.shape
}

export function styleFor(kind) {
  return FLOWCHART_KIND_STYLE[kind] ?? FALLBACK_STYLE
}

export function styleForNode(node) {
  const base = styleFor(node.kind)
  if (node.kind !== 'call' || node.fqn) return base
  return { ...base, dashed: true }
}
