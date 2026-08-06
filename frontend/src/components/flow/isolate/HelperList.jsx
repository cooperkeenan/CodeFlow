import { MONO, TEXT, TEXT_MUTED } from '../styles'

const HEAD = { fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', color: TEXT_MUTED, margin: '12px 0 5px' }

export default function HelperList({ helpers }) {
  if (!helpers?.length) return null
  return (
    <>
      <div style={HEAD}>Uses</div>
      {helpers.map(h => (
        <div key={h.fqn || h.name} data-helper={h.fqn} style={{ display: 'flex', gap: 10, padding: '2px 0' }}>
          <span style={{ fontFamily: MONO, fontSize: 11, color: TEXT, flex: '0 0 140px', wordBreak: 'break-all' }}>{h.name}</span>
          <span style={{ fontFamily: 'Instrument Sans, sans-serif', fontSize: 11, color: 'rgba(255,255,255,0.6)', lineHeight: 1.5 }}>{h.summary}</span>
        </div>
      ))}
    </>
  )
}
