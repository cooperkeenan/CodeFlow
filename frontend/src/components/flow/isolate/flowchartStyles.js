import { KIND, STATUS, alphaHex } from '../../../design/tokens'
import { SURFACE_2, TEXT_MUTED } from '../styles'

const FILL = '29'

export const FLOWCHART_KIND_STYLE = {
  start: { fill: alphaHex(KIND.entry, FILL), stroke: KIND.entry, shape: 'pill' },
  end: { fill: alphaHex(KIND.outcome, FILL), stroke: KIND.outcome, shape: 'pill' },
  call: { fill: alphaHex(KIND.step, FILL), stroke: KIND.step, shape: 'rect' },
  effect: { fill: alphaHex(KIND.effect, FILL), stroke: KIND.effect, shape: 'rect' },
  decision: { fill: alphaHex(KIND.decision, FILL), stroke: KIND.decision, shape: 'diamond' },
  loop: { fill: alphaHex(KIND.loop, FILL), stroke: KIND.loop, shape: 'rect' },
  return: { fill: alphaHex(KIND.outcome, FILL), stroke: KIND.outcome, shape: 'pill' },
  raise: { fill: alphaHex(STATUS.danger, FILL), stroke: STATUS.danger, shape: 'notch' },
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
