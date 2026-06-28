const LABEL = {
  fontFamily: 'IBM Plex Mono, monospace',
  fontSize: 9,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
  color: 'rgba(255,255,255,0.38)',
  marginBottom: 5,
}
const VALUE = {
  fontFamily: 'IBM Plex Mono, monospace',
  fontSize: 10,
  color: 'rgba(255,255,255,0.87)',
  lineHeight: 1.7,
}

export default function RationaleBox({ rationale, type }) {
  if (!rationale) return null
  return (
    <div style={{
      background: '#121212',
      border: '1px solid #242424',
      borderRadius: 3,
      padding: '0.75rem 1rem',
      display: 'flex',
      gap: '1.5rem',
      flexShrink: 0,
    }}>
      {type && (
        <div style={{ flexShrink: 0 }}>
          <div style={LABEL}>diagram type</div>
          <span style={VALUE}>{type}</span>
        </div>
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={LABEL}>selection rationale</div>
        <p style={{ ...VALUE, margin: 0 }}>{rationale}</p>
      </div>
    </div>
  )
}
