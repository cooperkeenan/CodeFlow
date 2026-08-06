import { MONO, TEXT_MUTED } from './styles'

const HIT_FLOOR = 0.72

const BASE = {
  fontFamily: MONO,
  borderRadius: 2,
  cursor: 'pointer',
  userSelect: 'none',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  border: '1px solid rgba(255,255,255,0.24)',
  background: 'transparent',
  color: TEXT_MUTED,
}

export default function IsolateButton({ onIsolate, nodeId, scale = 1 }) {
  const s = Math.max(scale, HIT_FLOOR)
  return (
    <span
      role="button"
      title="isolate this node"
      className="nodrag nopan"
      data-testid="isolate-button"
      style={{
        ...BASE,
        fontSize: Math.round(9 * s * 10) / 10,
        lineHeight: `${Math.round(13 * s)}px`,
        height: Math.round(15 * s),
        padding: `0 ${Math.round(5 * s)}px`,
      }}
      onPointerDown={event => {
        event.stopPropagation()
        event.preventDefault()
        onIsolate?.(nodeId)
      }}
      onClick={event => {
        event.stopPropagation()
        event.preventDefault()
      }}
    >
      isolate
    </span>
  )
}
