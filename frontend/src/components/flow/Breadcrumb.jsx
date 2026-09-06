import { MONO } from './styles'
import { viewLabel } from './linkLabels'

const MUTED = { fontFamily: MONO, fontSize: 12, color: 'rgba(255,255,255,0.38)' }
const CURRENT_STYLE = { fontFamily: MONO, fontSize: 12, color: 'rgba(255,255,255,0.6)' }
const MAX_SHOWN = 3

function collapseTrail(trail) {
  if (trail.length <= MAX_SHOWN) return trail.map((step, index) => ({ ...step, index }))
  const first = { ...trail[0], index: 0 }
  const lastTwo = trail.slice(-2).map((step, i) => ({ ...step, index: trail.length - 2 + i }))
  return [first, { ellipsis: true }, ...lastTwo]
}

export default function Breadcrumb({ trail, currentTitle, home, onBack, onNavigate }) {
  const shown = collapseTrail(trail)
  const backTo = trail.length ? () => onNavigate(trail.length - 1) : onBack

  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
      <button className="back" onClick={backTo} aria-label="back one level">←</button>
      <button className="back" onClick={onBack}>endpoints</button>
      {shown.map((step, i) =>
        step.ellipsis ? (
          <span key={`ellipsis-${i}`} style={MUTED}>/ …</span>
        ) : (
          <span key={`${step.kind}:${step.value}`} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={MUTED}>/</span>
            <button className="back" onClick={() => onNavigate(step.index)}>
              {viewLabel(step.kind, step.value, home)}
            </button>
          </span>
        )
      )}
      <span style={MUTED}>/</span>
      <span style={CURRENT_STYLE}>{currentTitle}</span>
    </span>
  )
}
