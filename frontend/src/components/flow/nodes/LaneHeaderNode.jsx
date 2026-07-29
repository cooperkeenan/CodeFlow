import { MONO, TEXT_MUTED } from '../styles'

export default function LaneHeaderNode({ data }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '4px 10px',
      pointerEvents: 'none',
      userSelect: 'none',
    }}>
      <span style={{
        fontFamily: MONO,
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: '0.14em',
        textTransform: 'uppercase',
        color: TEXT_MUTED,
        whiteSpace: 'nowrap',
      }}>
        {data.label}
      </span>
      <span style={{ flex: 1, height: 1, minWidth: 40, background: 'rgba(255,255,255,0.08)' }} />
    </div>
  )
}
