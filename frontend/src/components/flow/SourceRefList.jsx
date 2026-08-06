import { MONO, TEXT_MUTED, KIND_ACCENT } from './styles'

function blobUrl(base, ref) {
  if (!base) return null
  return `${base.replace(/\/$/, '')}/${ref.file}#L${ref.line}`
}

export default function SourceRefList({ refs, repoUrl }) {
  if (!refs?.length) {
    return <div style={{ fontFamily: MONO, fontSize: 10, color: TEXT_MUTED }}>no source refs</div>
  }
  return refs.map((ref, i) => {
    const href = blobUrl(repoUrl, ref)
    const text = `${ref.file}:${ref.line}`
    const style = { display: 'block', fontFamily: MONO, fontSize: 10, color: KIND_ACCENT.entry, lineHeight: 1.7, wordBreak: 'break-all' }
    return href
      ? <a key={i} href={href} target="_blank" rel="noreferrer" style={style}>{text}</a>
      : <div key={i} style={style}>{text}</div>
  })
}
