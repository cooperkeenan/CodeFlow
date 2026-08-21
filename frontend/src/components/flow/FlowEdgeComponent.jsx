import { BaseEdge, EdgeLabelRenderer, getBezierPath, getSmoothStepPath } from 'reactflow'
import { MONO, SURFACE_2, TEXT_MUTED } from './styles'
import EdgePacket from './EdgePacket'

const NORMAL = '#6C7689'
const STITCH = '#8A93A6'
const FLOW = '#39FF14'

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
  const lit = d.highlighted || d.packet || d.flowing
  const stroke = lit ? '#ffffff' : stitch ? STITCH : NORMAL
  const dashArray = stitch ? '2 5' : d.dashed ? '6 4' : undefined
  const width = (lit ? 2.4 : d.secondary ? 1 : 1.6) * scale
  const base = d.confidence === 'inferred' ? 0.6 : 1
  const opacity = d.dimmed ? 0.12 : lit ? 1 : d.near ? 0.55 : d.secondary ? base * 0.25 : base
  const markerId = `arrowhead-${id}`
  const markerSize = Math.max(5, Math.round(7 * scale))

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
      {d.entering ? (
        <path
          d={path}
          fill="none"
          stroke={stroke}
          strokeWidth={width}
          markerEnd={`url(#${markerId})`}
          pathLength="1"
          style={{ opacity, strokeDasharray: 1, strokeDashoffset: 1, animation: 'drawIn 700ms ease forwards' }}
        />
      ) : (
        <BaseEdge
          id={id}
          path={path}
          markerEnd={`url(#${markerId})`}
          style={{ stroke, strokeWidth: width, strokeDasharray: dashArray, opacity }}
        />
      )}
      {d.flowing && (
        <path
          d={path}
          fill="none"
          stroke={FLOW}
          strokeWidth={width * 1.15}
          strokeLinecap="round"
          strokeDasharray="8 10"
          style={{ animation: 'edgeFlow 900ms linear infinite', pointerEvents: 'none' }}
        />
      )}
      {d.packet && <EdgePacket key={`${id}-${d.stepKey}`} path={path} scale={scale} />}
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
              color: lit ? '#ffffff' : TEXT_MUTED,
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
