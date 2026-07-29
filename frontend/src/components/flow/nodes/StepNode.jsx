import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle } from '../styles'

const BASE = {
  width: 180,
  minHeight: 56,
  padding: '9px 13px',
  borderRadius: 3,
  background: SURFACE,
  display: 'flex',
  alignItems: 'center',
}

export default function StepNode({ data, selected }) {
  return (
    <div style={shellStyle(BASE, KIND_ACCENT.step, { selected, highlighted: data.highlighted, dashed: data.dashed })}>
      <Handles />
      <NodeChrome data={data} />
    </div>
  )
}
