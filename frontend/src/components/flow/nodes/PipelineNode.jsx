import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle, scalePad, revealStyle } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

const GLYPH_ISOLATED = { position: 'absolute', top: 10, left: 12, zIndex: 3 }

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
    isolated: data.isolated,
    focused: data.focused,
    dimmed: data.dimmed,
    adjacent: data.adjacent,
    entering: data.entering,
    enterDelay: data.enterDelay,
  })
  return (
    <div className={data.justRevealed ? 'rf-reveal-node' : undefined} style={{ ...style, ...revealStyle(data, KIND_ACCENT.pipeline) }}>
      <Handles target={targetPosition} source={sourcePosition} />
      <span
        title="pipeline step"
        style={{ color: KIND_ACCENT.pipeline, fontSize: Math.round(10 * scale), lineHeight: 1, flexShrink: 0, ...(data.isolated ? GLYPH_ISOLATED : {}) }}
      >
        ●
      </span>
      <NodeChrome data={data} />
    </div>
  )
}
