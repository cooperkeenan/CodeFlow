import { Handle, Position } from 'reactflow'

const LAYER_THEME = {
  presentation: { bg: '#0a1929', border: '#0d3b6e', accent: '#35a0f1', label: '#35a0f1' },
  business:     { bg: '#0a1f14', border: '#0d4a28', accent: '#35f1a0', label: '#35f1a0' },
  data:         { bg: '#1f130a', border: '#4a2e0d', accent: '#f1a035', label: '#f1a035' },
  external:     { bg: '#150a1f', border: '#3a0d4a', accent: '#c035f1', label: '#c035f1' },
}

const fallback = { bg: '#0f0f0f', border: '#2a2a2a', accent: '#c8f135', label: '#c8f135' }

export default function CustomNode({ data, selected }) {
  const theme = LAYER_THEME[data.layer] ?? fallback

  return (
    <div style={{
      background: theme.bg,
      border: `1px solid ${selected ? theme.accent : theme.border}`,
      borderRadius: 3,
      padding: '9px 13px',
      width: 190,
      boxShadow: data.isEntry ? `0 0 0 2px ${theme.accent}40` : 'none',
      outline: data.isEntry ? `1px solid ${theme.accent}` : 'none',
      outlineOffset: 3,
      transition: 'border-color 120ms ease',
      cursor: data.drillable ? 'pointer' : 'default',
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
        color: theme.label,
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
      }}>
        {data.actorType ?? data.layer}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: theme.border, width: 6, height: 6, border: 'none' }}
      />
    </div>
  )
}