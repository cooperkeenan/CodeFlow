export default function ClusterGroupNode({ data }) {
  const { color } = data
  return (
    <div style={{
      width: '100%', height: '100%',
      border: `1px solid ${color.border}66`,
      borderRadius: 5,
      background: `${color.bg}22`,
      pointerEvents: 'none',
      boxSizing: 'border-box',
    }}>
      <span style={{
        position: 'absolute', top: 4, left: 8,
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 9, letterSpacing: '0.06em',
        color: color.accent, fontWeight: 600,
        opacity: 0.85,
      }}>
        {data.label}
      </span>
    </div>
  )
}
