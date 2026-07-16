import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle } from '../styles'

const BASE = {
  minWidth: 150,
  maxWidth: 220,
  padding: '10px 18px',
  borderRadius: 999,
  background: SURFACE,
}

export default function EntryNode({ data, selected }) {
  return (
    <div style={shellStyle(BASE, KIND_ACCENT.entry, { selected, highlighted: data.highlighted })}>
      <Handles />
      <NodeChrome data={data} align="center" />
    </div>
  )
}
