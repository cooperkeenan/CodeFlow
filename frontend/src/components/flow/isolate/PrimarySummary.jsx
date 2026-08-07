import { MONO, TEXT, TEXT_MUTED, KIND_ACCENT } from '../styles'

const MARKER_STYLE = {
  fontSize: 9,
  color: KIND_ACCENT.entry,
  marginRight: 5,
  flexShrink: 0,
}

const NAME_STYLE = { color: KIND_ACCENT.entry }

export default function PrimarySummary({ primaryKind, primaryName, primarySummary, generated }) {
  if (!primaryName) return null
  const label = primaryKind ? primaryKind[0].toUpperCase() + primaryKind.slice(1) : 'Symbol'
  return (
    <div>
      <div style={{ fontFamily: MONO, fontSize: 12, fontWeight: 600, color: TEXT, display: 'flex', alignItems: 'baseline' }}>
        <span style={MARKER_STYLE}>◆</span>
        <span>
          {label}: <span style={NAME_STYLE}>{primaryName}</span>
        </span>
        {generated === false && (
          <span style={{ fontFamily: MONO, fontSize: 9, color: TEXT_MUTED, marginLeft: 6 }}>(heuristic)</span>
        )}
      </div>
      {primarySummary && (
        <p style={{ fontFamily: 'Instrument Sans, sans-serif', fontSize: 12, color: 'rgba(255,255,255,0.6)', lineHeight: 1.6, margin: '6px 0 0' }}>
          {primarySummary}
        </p>
      )}
    </div>
  )
}
