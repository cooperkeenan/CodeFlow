const SECTION = { marginBottom: 14 }
const LABEL = {
  fontFamily: 'IBM Plex Mono, monospace',
  fontSize: 9,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
  color: '#3a3a3a',
  marginBottom: 5,
}
const VALUE = {
  fontFamily: 'IBM Plex Mono, monospace',
  fontSize: 10,
  color: '#c8c8c8',
  lineHeight: 1.7,
}
const FILE = { ...VALUE, color: '#c8f135', wordBreak: 'break-all' }

export default function DetailPanel({ data, onClose }) {
  return (
    <aside style={{
      width: 260,
      flexShrink: 0,
      background: '#0c0c0c',
      border: '1px solid #1a1a1a',
      borderRadius: 3,
      padding: '1.1rem',
      overflow: 'auto',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <span style={{
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 12,
          fontWeight: 600,
          color: '#e2e2e2',
          lineHeight: 1.4,
        }}>
          {data.label}
        </span>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: '#3a3a3a',
            cursor: 'pointer',
            fontSize: 16,
            lineHeight: 1,
            padding: 0,
            flexShrink: 0,
            marginLeft: 8,
          }}
        >
          ×
        </button>
      </div>

      {data.description && (
        <div style={SECTION}>
          <div style={LABEL}>description</div>
          <p style={{
            fontFamily: 'Instrument Sans, sans-serif',
            fontSize: 12,
            color: '#888',
            lineHeight: 1.65,
            margin: 0,
          }}>
            {data.description}
          </p>
        </div>
      )}

      {data.file_path && (
        <div style={SECTION}>
          <div style={LABEL}>file</div>
          <span style={FILE}>{data.file_path}</span>
        </div>
      )}

      {data.io?.inputs?.length > 0 && (
        <div style={SECTION}>
          <div style={LABEL}>inputs</div>
          {data.io.inputs.map(i => <div key={i} style={VALUE}>{i}</div>)}
        </div>
      )}

      {data.io?.outputs?.length > 0 && (
        <div style={SECTION}>
          <div style={LABEL}>outputs</div>
          {data.io.outputs.map(o => <div key={o} style={VALUE}>{o}</div>)}
        </div>
      )}

      {data.actorType && (
        <div style={SECTION}>
          <div style={LABEL}>type</div>
          <span style={VALUE}>{data.actorType}</span>
        </div>
      )}
    </aside>
  )
}