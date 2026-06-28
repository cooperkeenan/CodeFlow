export default function ZoneGroupNode({ data }) {
  const { color } = data
  return (
    <div style={{
      width: '100%', height: '100%',
      border: `1px dashed ${color.border}`,
      borderRadius: 4,
      background: 'transparent',
      pointerEvents: 'none',
      boxSizing: 'border-box',
    }}>
      <span style={{
        position: 'absolute', top: 5, left: 9,
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 8, letterSpacing: '0.14em',
        textTransform: 'uppercase',
        color: 'rgba(255,255,255,0.60)', fontWeight: 600,
      }}>
        {data.label}
      </span>
    </div>
  )
}
