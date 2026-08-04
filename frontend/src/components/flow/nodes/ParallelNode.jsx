import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle, scalePad } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

export default function ParallelNode({ data, selected, sourcePosition, targetPosition }) {
  const { width, height } = data.geometry ?? GEOMETRY_FALLBACK.split_bar
  const scale = data.scale ?? 1
  const base = {
    width,
    minHeight: height,
    padding: scalePad(7, 12, scale),
    borderRadius: 3,
    background: `linear-gradient(90deg, ${KIND_ACCENT.parallel}22, ${SURFACE} 40%)`,
    display: 'flex',
    alignItems: 'center',
    gap: Math.round(8 * scale),
    boxSizing: 'border-box',
  }
  const style = shellStyle(base, KIND_ACCENT.parallel, { selected, highlighted: data.highlighted })
  return (
    <div style={{ ...style, borderLeft: `${Math.max(2, Math.round(4 * scale))}px solid ${KIND_ACCENT.parallel}` }}>
      <Handles target={targetPosition} source={sourcePosition} />
      <span title="parallel split" style={{ color: KIND_ACCENT.parallel, fontSize: Math.round(13 * scale), lineHeight: 1, flexShrink: 0 }}>⑃</span>
      <NodeChrome data={data} />
    </div>
  )
}
