import ClippedShape from '../ClippedShape'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT } from '../styles'

const DIAMOND = 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'
const TRAPEZOID = 'polygon(16% 0%, 84% 0%, 100% 100%, 0% 100%)'

export default function DecisionNode({ data, selected }) {
  const trapezoid = data.shape === 'trapezoid'
  return (
    <ClippedShape
      width={trapezoid ? 184 : 156}
      height={trapezoid ? 74 : 104}
      clipPath={trapezoid ? TRAPEZOID : DIAMOND}
      accent={KIND_ACCENT.decision}
      selected={selected}
      highlighted={data.highlighted}
    >
      <NodeChrome data={data} align="center" />
    </ClippedShape>
  )
}
