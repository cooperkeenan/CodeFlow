import { MONO, TEXT, TEXT_MUTED } from '../styles'

export default function PrimarySummary({ primaryKind, primaryName, primarySummary, generated }) {
  if (!primaryName) return null
  const label = primaryKind ? primaryKind[0].toUpperCase() + primaryKind.slice(1) : 'Symbol'
  return (
    <div>
      <div style={{ fontFamily: MONO, fontSize: 12, fontWeight: 600, color: TEXT }}>
        {label}: {primaryName}
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
