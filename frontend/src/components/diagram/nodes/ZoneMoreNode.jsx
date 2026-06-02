export default function ZoneMoreNode({ data }) {
  const { color, count, expanded } = data
  return (
    <div style={{
      width: 180, height: 58,
      border: `1px dashed ${color.border}`,
      borderRadius: 3,
      background: `${color.bg}40`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      cursor: 'pointer', boxSizing: 'border-box',
      fontFamily: 'IBM Plex Mono, monospace',
      fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
      color: color.accent,
    }}>
      {expanded ? '− show less' : `+${count} more`}
    </div>
  )
}
