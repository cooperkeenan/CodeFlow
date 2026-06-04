import { Handle, Position } from 'reactflow'

export default function ModuleSummaryNode({ data, selected }) {
  const { color, zoneCount = 0, componentCount = 0 } = data
  return (
    <div style={{
      width: 240, height: 110,
      background: color.bg,
      border: `1px solid ${selected ? color.accent : color.border}`,
      borderRadius: 6,
      padding: '14px 18px',
      cursor: 'pointer',
      boxShadow: `0 0 0 1px ${color.bg}, inset 0 0 0 1px ${color.border}55`,
      display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
      boxSizing: 'border-box',
    }}>
      <Handle type="target" position={Position.Top} style={{ opacity: 0, width: 1, height: 1, border: 'none', background: 'transparent', minWidth: 0, minHeight: 0 }} />
      <div style={{
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 16, fontWeight: 700,
        color: color.accent, letterSpacing: '0.02em',
      }}>
        {data.label}
      </div>
      <div style={{
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 10, color: 'rgba(255,255,255,0.60)', letterSpacing: '0.08em',
        textTransform: 'uppercase',
      }}>
        {zoneCount} {zoneCount === 1 ? 'zone' : 'zones'} · {componentCount} {componentCount === 1 ? 'component' : 'components'}
      </div>
      <div style={{
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 9, color: color.accent, opacity: 0.75,
        letterSpacing: '0.12em', textTransform: 'uppercase',
      }}>
        click to drill in ↓
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0, width: 1, height: 1, border: 'none', background: 'transparent', minWidth: 0, minHeight: 0 }} />
    </div>
  )
}
