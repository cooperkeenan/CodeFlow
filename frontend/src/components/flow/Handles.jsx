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

export default function Handles({ target = Position.Top, source = Position.Bottom }) {
  return (
    <>
      <Handle type="target" position={target} style={HIDDEN} />
      <Handle type="source" position={source} style={HIDDEN} />
    </>
  )
}
