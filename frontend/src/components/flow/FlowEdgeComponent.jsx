import { BaseEdge, EdgeLabelRenderer, getSmoothStepPath } from 'reactflow'
import { MONO, SURFACE_2, TEXT_MUTED } from './styles'

const SPINE = '#8fb8ff'
const NORMAL = '#4a4a4a'
const STITCH = '#6a6a6a'

export default function FlowEdgeComponent({
  id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data, label,
}) {
  const d = data ?? {}
  const stitch = d.kind === 'stitch' || d.routed === 'gutter'
  const [path, labelX, labelY] = getSmoothStepPath({
    sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition,
    borderRadius: stitch ? 2 : 8,
    offset: stitch ? 28 : 12,
  })

  const stroke = d.highlighted ? '#ffffff' : stitch ? STITCH : d.isSpine ? SPINE : NORMAL
  const dashArray = stitch ? '2 5' : d.dashed ? '6 4' : undefined
  const width = d.highlighted ? 3 : d.isSpine ? 2.5 : 1.4
  const opacity = d.confidence === 'inferred' ? 0.6 : 1

  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        style={{ stroke, strokeWidth: width, strokeDasharray: dashArray, opacity }}
      />
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              fontFamily: MONO,
              fontSize: 9,
              color: d.highlighted ? '#ffffff' : TEXT_MUTED,
              background: SURFACE_2,
              padding: '1px 4px',
              borderRadius: 2,
              opacity,
              pointerEvents: 'none',
            }}
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  )
}
