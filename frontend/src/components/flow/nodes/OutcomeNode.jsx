import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle, scalePad } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

export default function OutcomeNode({ data, selected, sourcePosition, targetPosition }) {
  const { width, height } = data.geometry ?? GEOMETRY_FALLBACK.outcome
  const base = {
    width,
    minHeight: height,
    padding: scalePad(8, 12, data.scale ?? 1),
    borderRadius: 10,
    background: SURFACE,
    display: 'flex',
    alignItems: 'center',
    boxSizing: 'border-box',
  }
  return (
    <div style={shellStyle(base, KIND_ACCENT.outcome, { selected, highlighted: data.highlighted, dashed: data.dashed, isolated: data.isolated })}>
      <Handles target={targetPosition} source={sourcePosition} />
      <NodeChrome data={data} align="center" />
    </div>
  )
}
