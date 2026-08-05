const HIT_FLOOR = 0.72

const BASE = {
  fontFamily: 'IBM Plex Mono, monospace',
  borderRadius: 2,
  cursor: 'pointer',
  userSelect: 'none',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  border: '1px solid #C98A3A',
  background: '#2A1F12',
  color: '#E5A44E',
}

export default function ExpandToggle({ expanded, count, onToggle, nodeId, scale = 1 }) {
  const s = Math.max(scale, HIT_FLOOR)
  return (
    <span
      role="button"
      title={expanded ? 'collapse decisions' : `reveal ${count} decision${count === 1 ? '' : 's'}`}
      className="nodrag nopan"
      style={{
        ...BASE,
        fontSize: Math.round(10 * s * 10) / 10,
        lineHeight: `${Math.round(13 * s)}px`,
        minWidth: Math.round(15 * s),
        height: Math.round(15 * s),
        padding: `0 ${Math.round(3 * s)}px`,
      }}
      onPointerDown={event => {
        event.stopPropagation()
        event.preventDefault()
        onToggle?.(nodeId)
      }}
      onClick={event => {
        event.stopPropagation()
        event.preventDefault()
      }}
    >
      {expanded ? '−' : `+${count}`}
    </span>
  )
}
