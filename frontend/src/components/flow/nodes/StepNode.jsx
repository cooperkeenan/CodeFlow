import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, shellStyle, scalePad, revealStyle } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

export default function StepNode({ data, selected, sourcePosition, targetPosition }) {
  const { width, height } = data.geometry ?? GEOMETRY_FALLBACK.rect
  const base = {
    width,
    minHeight: height,
    padding: scalePad(9, 13, data.scale ?? 1),
    borderRadius: 3,
    background: SURFACE,
    display: 'flex',
    alignItems: 'center',
    boxSizing: 'border-box',
  }
  return (
    <div
      className={data.justRevealed ? 'rf-reveal-node' : undefined}
      style={{
        ...shellStyle(base, KIND_ACCENT.step, { selected, highlighted: data.highlighted, dashed: data.dashed, isolated: data.isolated }),
        ...revealStyle(data, KIND_ACCENT.step),
      }}
    >
      <Handles target={targetPosition} source={sourcePosition} />
      <NodeChrome data={data} />
    </div>
  )
}
