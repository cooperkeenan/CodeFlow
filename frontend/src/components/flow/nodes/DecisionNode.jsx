import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle, scalePad } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

export default function DecisionNode({ data, selected, sourcePosition, targetPosition }) {
  const { width, height } = data.geometry ?? GEOMETRY_FALLBACK.decision
  const scale = data.scale ?? 1
  const base = {
    width,
    minHeight: height,
    padding: scalePad(8, 12, scale),
    borderRadius: 3,
    background: SURFACE,
    display: 'flex',
    alignItems: 'center',
    gap: Math.round(8 * scale),
    boxSizing: 'border-box',
  }
  const style = shellStyle(base, KIND_ACCENT.decision, {
    selected,
    highlighted: data.highlighted,
    dashed: data.dashed,
    isolated: data.isolated,
  })
  const shell = data.isolated
    ? style
    : { ...style, borderLeft: `${Math.max(2, Math.round(4 * scale))}px solid ${KIND_ACCENT.decision}` }
  return (
    <div style={shell}>
      <Handles target={targetPosition} source={sourcePosition} />
      <span
        title="decision"
        style={{ color: KIND_ACCENT.decision, fontSize: Math.round(12 * scale), lineHeight: 1, flexShrink: 0 }}
      >
        ◇
      </span>
      <NodeChrome data={data} />
    </div>
  )
}
