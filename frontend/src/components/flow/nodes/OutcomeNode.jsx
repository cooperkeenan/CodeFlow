import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle, scalePad } from '../styles'

const FALLBACK = { width: 160, height: 52 }

export default function OutcomeNode({ data, selected, sourcePosition, targetPosition }) {
  const { width, height } = data.geometry ?? FALLBACK
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
    <div style={shellStyle(base, KIND_ACCENT.outcome, { selected, highlighted: data.highlighted, dashed: data.dashed })}>
      <Handles target={targetPosition} source={sourcePosition} />
      <NodeChrome data={data} align="center" />
    </div>
  )
}
