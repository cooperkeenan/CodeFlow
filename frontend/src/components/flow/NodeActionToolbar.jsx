import { NodeToolbar, Position } from 'reactflow'
import { MONO, SURFACE_2, BORDER, TEXT_MUTED } from './styles'

const BUTTON_STYLE = {
  fontFamily: MONO,
  fontSize: 12,
  lineHeight: '18px',
  padding: '4px 10px',
  borderRadius: 3,
  cursor: 'pointer',
  background: SURFACE_2,
  border: `1px solid ${BORDER}`,
  color: TEXT_MUTED,
}

export default function NodeActionToolbar({ nodeId, onIsolate, isolated }) {
  if (!nodeId || !onIsolate) return null
  return (
    <NodeToolbar nodeId={nodeId} isVisible position={Position.Top} offset={10}>
      <button
        type="button"
        className="nodrag nopan"
        data-testid="isolate-action"
        style={BUTTON_STYLE}
        onClick={() => onIsolate(nodeId)}
      >
        {isolated ? 'close' : 'isolate'}
      </button>
    </NodeToolbar>
  )
}
