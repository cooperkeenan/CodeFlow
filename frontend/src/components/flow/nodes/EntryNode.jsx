import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle, scalePad } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

export default function EntryNode({ data, selected, sourcePosition, targetPosition }) {
  const { width, height } = data.geometry ?? GEOMETRY_FALLBACK.pill
  const base = {
    width,
    minHeight: height,
    padding: scalePad(10, 18, data.scale ?? 1),
    borderRadius: 999,
    background: SURFACE,
    display: 'flex',
    alignItems: 'center',
    boxSizing: 'border-box',
  }
  return (
    <div style={shellStyle(base, KIND_ACCENT.entry, { selected, highlighted: data.highlighted, focused: data.focused, dimmed: data.dimmed, adjacent: data.adjacent })}>
      <Handles target={targetPosition} source={sourcePosition} />
      <NodeChrome data={data} align="center" />
    </div>
  )
}
