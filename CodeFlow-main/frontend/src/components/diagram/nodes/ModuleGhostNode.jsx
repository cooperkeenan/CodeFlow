import { Handle, Position } from 'reactflow'

export default function ModuleGhostNode({ data }) {
  const { color } = data
  return (
    <div style={{
      width: 240, height: 60,
      background: color.bg,
      border: `1px dashed ${color.border}`,
      borderRadius: 4,
      padding: '10px 14px',
      opacity: 0.7,
      cursor: 'default',
      boxSizing: 'border-box',
      display: 'flex', flexDirection: 'column', justifyContent: 'center',
    }}>
      <Handle type="target" position={Position.Left} style={{ opacity: 0, width: 1, height: 1, border: 'none', background: 'transparent', minWidth: 0, minHeight: 0 }} />
      <div style={{
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 12, fontWeight: 600,
        color: color.accent, letterSpacing: '0.04em',
      }}>
        {data.label}
      </div>
      <div style={{
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 8, color: 'rgba(255,255,255,0.38)', letterSpacing: '0.12em',
        textTransform: 'uppercase',
      }}>
        neighbour
      </div>
      <Handle type="source" position={Position.Right} style={{ opacity: 0, width: 1, height: 1, border: 'none', background: 'transparent', minWidth: 0, minHeight: 0 }} />
    </div>
  )
}
