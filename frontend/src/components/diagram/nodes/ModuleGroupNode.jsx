export default function ModuleGroupNode({ data }) {
  const { color } = data
  return (
    <div style={{
      width: '100%', height: '100%',
      border: `1px solid ${color.border}`,
      borderRadius: 6,
      background: `${color.bg}55`,
      pointerEvents: 'none',
      boxSizing: 'border-box',
    }}>
      <span
        className="nodrag"
        title="Click to focus this module"
        style={{
          position: 'absolute', top: 6, left: 10,
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 11, letterSpacing: '0.08em',
          color: color.accent, fontWeight: 700,
          pointerEvents: 'auto', cursor: 'pointer',
          padding: '2px 4px', borderRadius: 3,
        }}
      >
        {data.label} <span style={{ opacity: 0.5, fontSize: 9 }}>⤢</span>
      </span>
    </div>
  )
}
