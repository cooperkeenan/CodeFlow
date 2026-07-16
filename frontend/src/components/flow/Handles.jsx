import { Handle, Position } from 'reactflow'

const HIDDEN = {
  opacity: 0,
  width: 1,
  height: 1,
  minWidth: 0,
  minHeight: 0,
  border: 'none',
  background: 'transparent',
}

export default function Handles() {
  return (
    <>
      <Handle type="target" position={Position.Left} style={HIDDEN} />
      <Handle type="target" position={Position.Top} style={HIDDEN} />
      <Handle type="source" position={Position.Right} style={HIDDEN} />
      <Handle type="source" position={Position.Bottom} style={HIDDEN} />
    </>
  )
}
