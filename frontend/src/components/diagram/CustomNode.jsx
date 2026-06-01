import { Handle, Position } from 'reactflow'

const FALLBACK = { bg: '#0f0f0f', border: '#2a2a2a', accent: '#c8f135' }

export default function CustomNode({ data, selected }) {
  const theme = data.color ?? FALLBACK

  return (
    <div style={{
      background: theme.bg,
      border: `1px solid ${selected ? theme.accent : theme.border}`,
      borderRadius: 3,
      padding: '9px 13px',
      width: 180,
      boxShadow: data.isEntry ? `0 0 0 2px ${theme.accent}40` : 'none',
      outline: data.isEntry ? `1px solid ${theme.accent}` : 'none',
      outlineOffset: 3,
      transition: 'border-color 120ms ease',
      cursor: 'pointer',
    }}>
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: theme.border, width: 6, height: 6, border: 'none' }}
      />

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 6 }}>
        <span style={{
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 11,
          fontWeight: 600,
          color: '#d8d8d8',
          lineHeight: 1.4,
          wordBreak: 'break-all',
        }}>
          {data.label}
        </span>

        {data.drillable && (
          <span style={{
            flexShrink: 0,
            fontFamily: 'IBM Plex Mono, monospace',
            fontSize: 8,
            fontWeight: 600,
            letterSpacing: '0.08em',
            color: theme.accent,
            border: `1px solid ${theme.border}`,
            borderRadius: 2,
            padding: '2px 4px',
            marginTop: 1,
          }}>
            ↓
          </span>
        )}
      </div>

      <div style={{
        marginTop: 4,
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 9,
        color: theme.accent,
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
      }}>
        {data.actorType ?? data.zone}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: theme.border, width: 6, height: 6, border: 'none' }}
      />
    </div>
  )
}
