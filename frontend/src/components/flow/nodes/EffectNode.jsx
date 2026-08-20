import Handles from '../Handles'
import NodeChrome from '../NodeChrome'
import { KIND_ACCENT, SURFACE, EFFECT_ICON, shellStyle, scalePad } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

export default function EffectNode({ data, selected, sourcePosition, targetPosition }) {
  const icon = EFFECT_ICON[data.effectKind] ?? '◆'
  const { width, height } = data.geometry ?? GEOMETRY_FALLBACK.effect
  const scale = data.scale ?? 1
  const base = {
    width,
    minHeight: height,
    padding: scalePad(9, 12, scale),
    borderRadius: 8,
    background: SURFACE,
    display: 'flex',
    alignItems: 'center',
    gap: Math.round(9 * scale),
    boxSizing: 'border-box',
  }
  return (
    <div style={shellStyle(base, KIND_ACCENT.effect, { selected, highlighted: data.highlighted, dashed: data.dashed, focused: data.focused, dimmed: data.dimmed, adjacent: data.adjacent })}>
      <Handles target={targetPosition} source={sourcePosition} />
      <span title={data.effectKind ?? 'effect'} style={{ fontSize: Math.round(16 * scale), lineHeight: 1, flexShrink: 0 }}>{icon}</span>
      <NodeChrome data={data} subtitle={data.effectTarget || null} />
    </div>
  )
}
