import { MONO, TEXT, TEXT_MUTED, KIND_ACCENT } from '../flow/styles'

const SANS = 'Instrument Sans, sans-serif'
const HEAD = {
  fontFamily: MONO, fontSize: 9, letterSpacing: '0.14em', textTransform: 'uppercase',
  color: 'rgba(255,255,255,0.34)', margin: '0 0 8px',
}

export function Section({ title, children, compact = false }) {
  return (
    <div style={{ marginTop: compact ? 10 : 22, paddingTop: compact ? 8 : 16, borderTop: '1px solid rgba(255,255,255,0.07)' }}>
      <div style={HEAD}>{title}</div>
      {children}
    </div>
  )
}

export function Facts({ facts }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {facts.map(fact => (
        <div
          key={fact.label}
          style={{
            flex: '1 1 90px', background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.07)', borderRadius: 3, padding: '7px 9px',
          }}
        >
          <div style={{ fontFamily: MONO, fontSize: 13, fontWeight: 600, color: TEXT }}>
            {fact.value}
          </div>
          <div style={{ fontFamily: MONO, fontSize: 9, color: TEXT_MUTED, marginTop: 2 }}>
            {fact.label}
          </div>
        </div>
      ))}
    </div>
  )
}

export function Branches({ branches }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
      {branches.map(branch => (
        <div key={branch.label} style={{ display: 'flex', gap: 9, alignItems: 'baseline' }}>
          <span
            style={{
              fontFamily: MONO, fontSize: 9, padding: '2px 6px', borderRadius: 2, flexShrink: 0,
              color: branch.terminal ? TEXT_MUTED : KIND_ACCENT.entry,
              border: `1px solid ${branch.terminal ? 'rgba(255,255,255,0.14)' : KIND_ACCENT.entry + '55'}`,
            }}
          >
            {branch.terminal ? 'stops' : 'rejoins'}
          </span>
          <span style={{ minWidth: 0 }}>
            <span style={{ fontFamily: MONO, fontSize: 11, color: TEXT }}>{branch.target}</span>
            {branch.note && (
              <span style={{ fontFamily: SANS, fontSize: 11, color: TEXT_MUTED, display: 'block', lineHeight: 1.5 }}>
                {branch.note}
              </span>
            )}
          </span>
        </div>
      ))}
    </div>
  )
}

export function Refs({ refs, repoUrl }) {
  return refs.map((item, index) => {
    const text = `${item.file}:${item.line}`
    const href = repoUrl ? `${repoUrl.replace(/\/$/, '')}/${item.file}#L${item.line}` : null
    const style = {
      display: 'block', fontFamily: MONO, fontSize: 10, color: KIND_ACCENT.entry,
      lineHeight: 1.8, wordBreak: 'break-all', textDecoration: 'none',
    }
    return href
      ? <a key={index} href={href} target="_blank" rel="noreferrer" style={style}>{text}</a>
      : <span key={index} style={style}>{text}</span>
  })
}
