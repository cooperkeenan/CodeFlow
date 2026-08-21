import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle, scalePad, revealStyle } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

const GLYPH_ISOLATED = { position: 'absolute', top: 10, left: 12, zIndex: 3 }

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
  const style = shellStyle(base, KIND_ACCENT.parallel, {
    selected,
    highlighted: data.highlighted,
    dashed: data.dashed,
    isolated: data.isolated, focused: data.focused, dimmed: data.dimmed, adjacent: data.adjacent, entering: data.entering, enterDelay: data.enterDelay,
  })
  const shell = data.isolated
    ? style
    : { ...style, borderLeft: `${Math.max(2, Math.round(4 * scale))}px solid ${KIND_ACCENT.parallel}` }
  return (
    <div className={data.justRevealed ? 'rf-reveal-node' : undefined} style={{ ...shell, ...revealStyle(data, KIND_ACCENT.parallel) }}>
      <Handles target={targetPosition} source={sourcePosition} />
      <span title="parallel split" style={{ color: KIND_ACCENT.parallel, fontSize: Math.round(13 * scale), lineHeight: 1, flexShrink: 0, ...(data.isolated ? GLYPH_ISOLATED : {}) }}>⑃</span>
      <NodeChrome data={data} />
    </div>
  )
}
