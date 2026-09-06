import { MONO, KIND_ACCENT } from './styles'
import { shortName } from './linkLabels'

const HIT_FLOOR = 0.72

export default function LinkChip({ link, onLink, nodeId, scale = 1 }) {
  const s = Math.max(scale, HIT_FLOOR)
  const accent = KIND_ACCENT[link.kind === 'helper' ? 'step' : 'entry']
  return (
    <span
      role="button"
      title={`open ${link.target}`}
      className="nodrag nopan"
      data-testid="link-chip"
      style={{
        fontFamily: MONO,
        borderRadius: 2,
        cursor: 'pointer',
        userSelect: 'none',
        display: 'inline-flex',
        alignItems: 'center',
        gap: Math.round(4 * s),
        maxWidth: '100%',
        border: `1px solid ${accent}88`,
        background: `${accent}1A`,
        color: accent,
        fontSize: Math.round(10 * s * 10) / 10,
        lineHeight: `${Math.round(15 * s)}px`,
        height: Math.round(17 * s),
        padding: `0 ${Math.round(6 * s)}px`,
        overflow: 'hidden',
        whiteSpace: 'nowrap',
        textOverflow: 'ellipsis',
        flexShrink: 0,
      }}
      onPointerDown={event => {
        event.stopPropagation()
        event.preventDefault()
        onLink?.(link, nodeId)
      }}
      onClick={event => {
        event.stopPropagation()
        event.preventDefault()
      }}
    >
      <span aria-hidden="true">→</span>
      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{shortName(link.target)}</span>
    </span>
  )
}
