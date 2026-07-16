import { MONO, SURFACE_2, BORDER, TEXT, TEXT_MUTED, KIND_ACCENT } from './styles'

const HEAD = { fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', color: TEXT_MUTED, margin: '12px 0 5px' }

function blobUrl(base, ref) {
  if (!base) return null
  return `${base.replace(/\/$/, '')}/${ref.file}#L${ref.line}`
}

export default function ProvenancePopover({ node, repoUrl, onClose }) {
  const data = node.data
  return (
    <aside style={{
      position: 'absolute', top: 12, right: 12, zIndex: 6, width: 300, maxHeight: 'calc(100% - 24px)',
      overflow: 'auto', background: SURFACE_2, border: `1px solid ${BORDER}`, borderRadius: 4, padding: '14px 16px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <span style={{ fontFamily: MONO, fontSize: 12, fontWeight: 600, color: TEXT, lineHeight: 1.4 }}>{data.label}</span>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: TEXT_MUTED, cursor: 'pointer', fontSize: 16, lineHeight: 1, padding: 0 }}>×</button>
      </div>

      {data.oneLiner && (
        <p style={{ fontFamily: 'Instrument Sans, sans-serif', fontSize: 12, color: 'rgba(255,255,255,0.6)', lineHeight: 1.6, margin: '8px 0 0' }}>
          {data.oneLiner}
        </p>
      )}

      {data.backing?.length > 0 && (
        <>
          <div style={HEAD}>backing</div>
          {data.backing.map(name => (
            <div key={name} style={{ fontFamily: MONO, fontSize: 10, color: TEXT, lineHeight: 1.7, wordBreak: 'break-all' }}>{name}</div>
          ))}
        </>
      )}

      <div style={HEAD}>source</div>
      {data.refs?.length > 0 ? data.refs.map((ref, i) => {
        const href = blobUrl(repoUrl, ref)
        const text = `${ref.file}:${ref.line}`
        return href
          ? <a key={i} href={href} target="_blank" rel="noreferrer" style={{ display: 'block', fontFamily: MONO, fontSize: 10, color: KIND_ACCENT.entry, lineHeight: 1.7, wordBreak: 'break-all' }}>{text}</a>
          : <div key={i} style={{ fontFamily: MONO, fontSize: 10, color: KIND_ACCENT.entry, lineHeight: 1.7, wordBreak: 'break-all' }}>{text}</div>
      }) : (
        <div style={{ fontFamily: MONO, fontSize: 10, color: TEXT_MUTED }}>no source refs</div>
      )}
    </aside>
  )
}
