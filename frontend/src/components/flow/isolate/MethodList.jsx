import { MONO, TEXT, TEXT_MUTED } from '../styles'

const HEAD = { fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', color: TEXT_MUTED, margin: '12px 0 5px' }

export default function MethodList({ methods }) {
  if (!methods?.length) return null
  return (
    <>
      <div style={HEAD}>Methods</div>
      {methods.map(m => (
        <div key={m.fqn || m.name} data-method={m.name} style={{ display: 'flex', gap: 10, padding: '2px 0' }}>
          <span style={{ fontFamily: MONO, fontSize: 11, color: TEXT, flex: '0 0 140px', wordBreak: 'break-all' }}>{m.name}</span>
          <span style={{ fontFamily: 'Instrument Sans, sans-serif', fontSize: 11, color: 'rgba(255,255,255,0.6)', lineHeight: 1.5 }}>{m.summary}</span>
        </div>
      ))}
    </>
  )
}
