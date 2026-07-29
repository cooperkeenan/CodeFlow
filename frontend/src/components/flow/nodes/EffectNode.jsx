import Handles from '../Handles'
import NodeBadges from '../NodeBadges'
import { KIND_ACCENT, SURFACE, MONO, LABEL_STYLE, TEXT_MUTED, EFFECT_ICON, shellStyle } from '../styles'

const BASE = {
  width: 184,
  minHeight: 50,
  padding: '9px 12px',
  borderRadius: 8,
  background: SURFACE,
  display: 'flex',
  alignItems: 'center',
  gap: 9,
}

export default function EffectNode({ data, selected }) {
  const icon = EFFECT_ICON[data.effectKind] ?? '◆'
  return (
    <div style={shellStyle(BASE, KIND_ACCENT.effect, { selected, highlighted: data.highlighted, dashed: data.dashed })}>
      <Handles />
      <span title={data.effectKind ?? 'effect'} style={{ fontSize: 16, lineHeight: 1, flexShrink: 0 }}>{icon}</span>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
        <span style={LABEL_STYLE}>{data.label}</span>
        {data.effectTarget && (
          <span style={{ fontFamily: MONO, fontSize: 8, color: TEXT_MUTED, wordBreak: 'break-all' }}>
            {data.effectTarget}
          </span>
        )}
        <NodeBadges badges={data.badges} guardSource={data.guardSource} />
      </div>
    </div>
  )
}
