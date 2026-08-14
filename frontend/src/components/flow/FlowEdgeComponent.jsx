import { BaseEdge, EdgeLabelRenderer, getBezierPath, getSmoothStepPath } from 'reactflow'
import { MONO, SURFACE_2, TEXT_MUTED } from './styles'

const NORMAL = '#4a4a4a'
const STITCH = '#6a6a6a'

export default function FlowEdgeComponent({
  id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data, label,
}) {
  const d = data ?? {}
  const stitch = d.kind === 'stitch' || d.routed === 'gutter'
  const geom = { sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition }
  const [path, labelX, labelY] = stitch
    ? getSmoothStepPath({ ...geom, borderRadius: 2, offset: 28 })
    : getBezierPath({ ...geom, curvature: 0.18 })

  const scale = d.scale ?? 1
  const stroke = d.highlighted ? '#ffffff' : stitch ? STITCH : NORMAL
  const dashArray = stitch ? '2 5' : d.dashed ? '6 4' : undefined
  const width = (d.highlighted ? 2.4 : d.secondary ? 1 : 1.6) * scale
  const base = d.confidence === 'inferred' ? 0.6 : 1
  const opacity = d.secondary ? base * 0.25 : base
  const markerId = `arrowhead-${id}`
  const markerSize = Math.max(5, Math.round(7 * scale))
  const canDraw = d.justRevealed && !stitch && !d.dashed

  return (
    <>
      <defs>
        <marker
          id={markerId}
          markerWidth={markerSize}
          markerHeight={markerSize}
          refX={markerSize - 0.5}
          refY={markerSize / 2}
          orient="auto-start-reverse"
          markerUnits="userSpaceOnUse"
        >
          <path d={`M0,0 L${markerSize},${markerSize / 2} L0,${markerSize} z`} fill={stroke} opacity={opacity} />
        </marker>
      </defs>
      {canDraw ? (
        <>
          <path
            id={id}
            d={path}
            fill="none"
            className="react-flow__edge-path rf-reveal-edge"
            markerEnd={`url(#${markerId})`}
            pathLength={100}
            style={{ stroke, strokeWidth: width, opacity, animationDelay: `${d.revealEdgeDelayMs ?? 0}ms` }}
          />
          <path d={path} fill="none" strokeOpacity={0} strokeWidth={20} className="react-flow__edge-interaction" />
        </>
      ) : (
        <BaseEdge
          id={id}
          path={path}
          markerEnd={`url(#${markerId})`}
          style={{ stroke, strokeWidth: width, strokeDasharray: dashArray, opacity }}
        />
      )}
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              fontFamily: MONO,
              fontSize: Math.round(9 * scale * 10) / 10,
              maxWidth: Math.round(160 * scale),
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              color: d.highlighted ? '#ffffff' : TEXT_MUTED,
              background: SURFACE_2,
              padding: `${Math.round(1 * scale)}px ${Math.round(4 * scale)}px`,
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
