import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle, scalePad } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

export default function PipelineNode({ data, selected, sourcePosition, targetPosition }) {
  const { width, height } = data.geometry ?? GEOMETRY_FALLBACK.pipeline
  const scale = data.scale ?? 1
  const base = {
    width,
    minHeight: height,
    padding: scalePad(6, 12, scale),
    borderRadius: 999,
    background: SURFACE,
    display: 'flex',
    alignItems: 'center',
    gap: Math.round(8 * scale),
    boxSizing: 'border-box',
  }
  const style = shellStyle(base, KIND_ACCENT.pipeline, {
    selected,
    highlighted: data.highlighted,
    dashed: data.dashed,
  })
  return (
    <div style={style}>
      <Handles target={targetPosition} source={sourcePosition} />
      <span
        title="pipeline step"
        style={{ color: KIND_ACCENT.pipeline, fontSize: Math.round(10 * scale), lineHeight: 1, flexShrink: 0 }}
      >
        ●
      </span>
      <NodeChrome data={data} />
    </div>
  )
}
