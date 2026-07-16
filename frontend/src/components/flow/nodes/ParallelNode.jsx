import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle } from '../styles'

const BASE = {
  width: 200,
  minHeight: 36,
  padding: '7px 12px',
  borderRadius: 3,
  background: `linear-gradient(90deg, ${KIND_ACCENT.parallel}22, ${SURFACE} 40%)`,
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  borderLeft: `4px solid ${KIND_ACCENT.parallel}`,
}

export default function ParallelNode({ data, selected }) {
  const style = shellStyle(BASE, KIND_ACCENT.parallel, { selected, highlighted: data.highlighted })
  return (
    <div style={{ ...style, borderLeft: BASE.borderLeft }}>
      <Handles />
      <span title="parallel split" style={{ color: KIND_ACCENT.parallel, fontSize: 13, lineHeight: 1 }}>⑃</span>
      <NodeChrome data={data} />
    </div>
  )
}
