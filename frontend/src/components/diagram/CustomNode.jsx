import { Handle, Position } from 'reactflow'

const FALLBACK = { bg: '#1A1A1A', border: '#333333', accent: '#39FF14' }

export default function CustomNode({ data, selected }) {
  const theme = data.color ?? FALLBACK

  return (
    <div style={{
      background: 'linear-gradient(0deg, rgba(255,255,255,0.06), rgba(255,255,255,0.06)), ' + theme.bg,
      border: `1px solid ${selected ? theme.accent : theme.accent + '66'}`,
      borderRadius: 3,
      padding: '9px 13px',
      width: 180,
      height: data.expanded ? 'auto' : 84,
      minHeight: 84,
      boxSizing: 'border-box',
      boxShadow: data.isEntry ? `0 0 0 2px ${theme.accent}40` : 'none',
      outline: data.isEntry ? `1px solid ${theme.accent}` : 'none',
      outlineOffset: 3,
      transition: 'border-color 120ms ease',
      cursor: 'pointer',
    }}>
      <Handle type="target" position={Position.Top} style={{ opacity: 0, width: 1, height: 1, border: 'none', background: 'transparent', minWidth: 0, minHeight: 0 }} />
      <Handle id="left" type="target" position={Position.Left} style={{ opacity: 0, width: 1, height: 1, border: 'none', background: 'transparent', minWidth: 0, minHeight: 0 }} />

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 6 }}>
        <span style={{
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 11,
          fontWeight: 600,
          color: 'rgba(255,255,255,0.87)',
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

      {data.description && (
        <div style={{
          marginTop: 5,
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 8,
          color: 'rgba(255,255,255,0.5)',
          lineHeight: 1.4,
          ...(data.expanded
            ? { overflow: 'visible' }
            : { overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }
          ),
        }}>
          {data.description}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} style={{ opacity: 0, width: 1, height: 1, border: 'none', background: 'transparent', minWidth: 0, minHeight: 0 }} />
      <Handle id="right" type="source" position={Position.Right} style={{ opacity: 0, width: 1, height: 1, border: 'none', background: 'transparent', minWidth: 0, minHeight: 0 }} />
    </div>
  )
}
