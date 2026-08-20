import { MONO, SURFACE_2 } from './styles'

const PACKET = '#39FF14'
const TRAIL = [0, 90, 180]

export default function EdgePacket({ path, scale = 1, duration = 2400 }) {
  const size = Math.max(16, Math.round(20 * scale))
  return (
    <g pointerEvents="none">
      {TRAIL.map((delay, index) => (
        <g key={delay} opacity={index === 0 ? 1 : 0.32 / index}>
          <rect
            x={-size * 1.05} y={-size * 0.62} width={size * 2.1} height={size * 1.24} rx={2}
            fill={index === 0 ? SURFACE_2 : 'none'} stroke={PACKET} strokeWidth={1.5}
          />
          {index === 0 && (
            <text
              y={size * 0.38} textAnchor="middle" fill={PACKET}
              style={{ fontFamily: MONO, fontSize: size, fontWeight: 700 }}
            >
              {'{ }'}
            </text>
          )}
          <animateMotion
            begin={`${delay}ms`}
            dur={`${duration}ms`}
            repeatCount="1"
            fill="freeze"
            calcMode="spline"
            keyPoints="0;1"
            keyTimes="0;1"
            keySplines="0.4 0 0.2 1"
            path={path}
          />
          <animate
            attributeName="opacity"
            begin={`${delay}ms`}
            dur={`${duration}ms`}
            repeatCount="1"
            fill="freeze"
            values={`0;${index === 0 ? 1 : 0.3};${index === 0 ? 1 : 0.3};0`}
            keyTimes="0;0.12;0.8;1"
          />
        </g>
      ))}
    </g>
  )
}
