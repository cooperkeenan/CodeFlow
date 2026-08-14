import { styleForNode } from './flowchartStyles'
import { displayLabel } from './flowchartLabel'
import { MONO, SURFACE_2, TEXT, TEXT_MUTED } from '../styles'

const LINE_H = 13

function breakPoint(window, maxChars) {
  for (const token of [' ', '.', '_']) {
    const at = window.lastIndexOf(token)
    if (at > 3) return at + 1
  }
  return maxChars
}

function wrapLabel(label, maxChars, maxLines) {
  const text = label ?? ''
  if (text.length <= maxChars) return [text]
  const lines = []
  let rest = text
  while (rest.length > 0 && lines.length < maxLines) {
    if (lines.length === maxLines - 1) {
      lines.push(rest.length > maxChars ? `${rest.slice(0, maxChars - 1)}…` : rest)
      break
    }
    const cut = breakPoint(rest.slice(0, maxChars), maxChars)
    lines.push(rest.slice(0, cut).trimEnd())
    rest = rest.slice(cut).trimStart()
  }
  return lines
}

function outline(node) {
  if (node.shape === 'diamond') {
    const { x, y, w, h } = node
    return <polygon points={`${x + w / 2},${y} ${x + w},${y + h / 2} ${x + w / 2},${y + h} ${x},${y + h / 2}`} />
  }
  const rx = node.shape === 'pill' ? node.h / 2 : 6
  return <rect x={node.x} y={node.y} width={node.w} height={node.h} rx={rx} />
}

function nodeTitle(node) {
  const parts = [node.raw ?? node.label]
  if (node.line) parts.push(`line ${node.line}`)
  if (node.kind === 'call' && !node.fqn) parts.push('target unresolved')
  else if (node.fqn) parts.push(node.fqn)
  return parts.join('\n')
}

export function FlowNode({ node }) {
  const style = styleForNode(node)
  const text = node.llmLabel || (node.raw ? node.label : displayLabel(node.label, node.kind))
  const lines = wrapLabel(text, node.shape === 'diamond' ? 15 : 24, 3)
  const cx = node.x + node.w / 2
  const top = node.y + node.h / 2 - ((lines.length - 1) * LINE_H) / 2
  return (
    <g fill={style.fill} stroke={style.stroke} strokeWidth={1.5} strokeDasharray={style.dashed ? '4 3' : undefined}>
      <title>{nodeTitle(node)}</title>
      {outline(node)}
      <text x={cx} y={top} textAnchor="middle" dominantBaseline="middle" fontFamily={MONO} fontSize={11} fill={TEXT} stroke="none">
        {lines.map((line, index) => (
          <tspan key={line + index} x={cx} dy={index === 0 ? 0 : LINE_H}>{line}</tspan>
        ))}
      </text>
    </g>
  )
}

export function FlowEdge({ edge }) {
  return (
    <g>
      <path d={edge.path} className={edge.className} fill="none" stroke={TEXT_MUTED} strokeWidth={1.4} markerEnd="url(#flowchart-arrow)" />
      {edge.label && (
        <text
          x={edge.labelX}
          y={edge.labelY - 5}
          textAnchor="middle"
          fontFamily={MONO}
          fontSize={9}
          fill={TEXT_MUTED}
          stroke={SURFACE_2}
          strokeWidth={3}
          paintOrder="stroke"
        >
          {edge.label}
        </text>
      )}
    </g>
  )
}
