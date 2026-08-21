import Handles from '../Handles'
import { KIND_ACCENT, SURFACE, TEXT, TEXT_MUTED, MONO, shellStyle } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

const SANS = 'Instrument Sans, sans-serif'

export default function CardNode({ data, selected, sourcePosition, targetPosition }) {
  const { width, height } = data.geometry ?? GEOMETRY_FALLBACK.card
  const accent = KIND_ACCENT.card
  const base = {
    width,
    minHeight: height,
    padding: '32px 40px',
    borderRadius: 6,
    background: SURFACE,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    boxSizing: 'border-box',
  }
  const style = shellStyle(base, accent, {
    selected,
    highlighted: data.highlighted,
    dashed: data.dashed,
    focused: data.focused,
    dimmed: data.dimmed,
    adjacent: data.adjacent,
    entering: data.entering,
    enterDelay: data.enterDelay,
  })
  const kicker = data.actNumber && data.actTotal ? `ACT ${data.actNumber} / ${data.actTotal}` : null
  const title = data.fullLabel ?? data.label
  return (
    <div style={style}>
      <Handles target={targetPosition} source={sourcePosition} />
      {kicker && (
        <span style={{ fontFamily: MONO, fontSize: 13, fontWeight: 600, letterSpacing: '0.18em', color: accent }}>
          {kicker}
        </span>
      )}
      <h2 style={{ fontFamily: SANS, fontSize: 34, fontWeight: 700, color: TEXT, margin: '14px 0 0', lineHeight: 1.15 }}>
        {title}
      </h2>
      <div style={{ width: 56, height: 3, background: accent, margin: '18px 0' }} />
      {data.oneLiner && (
        <p style={{ fontFamily: SANS, fontSize: 15, color: TEXT_MUTED, lineHeight: 1.55, margin: 0, maxWidth: width - 80 }}>
          {data.oneLiner}
        </p>
      )}
    </div>
  )
}
