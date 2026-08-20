import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle, scalePad } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

export default function StepNode({ data, selected, sourcePosition, targetPosition }) {
  const { width, height } = data.geometry ?? GEOMETRY_FALLBACK.rect
  const base = {
    width,
    minHeight: height,
    padding: scalePad(9, 13, data.scale ?? 1),
    borderRadius: 3,
    background: SURFACE,
    display: 'flex',
    alignItems: 'center',
    boxSizing: 'border-box',
  }
  return (
    <div style={shellStyle(base, KIND_ACCENT.step, { selected, highlighted: data.highlighted, dashed: data.dashed, focused: data.focused, dimmed: data.dimmed, adjacent: data.adjacent })}>
      <Handles target={targetPosition} source={sourcePosition} />
      <NodeChrome data={data} />
    </div>
  )
}
