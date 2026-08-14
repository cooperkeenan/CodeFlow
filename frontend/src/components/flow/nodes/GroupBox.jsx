import { KIND_ACCENT } from '../styles'

export default function GroupBox({ data }) {
  const accent = KIND_ACCENT[data.ownerKind] ?? KIND_ACCENT.decision
  const scale = data.scale ?? 1
  return (
    <div
      className={data.revealBacking ? 'rf-reveal-backing' : undefined}
      style={{
        width: data.width,
        height: data.height,
        border: `${Math.max(1, Math.round(scale))}px dashed ${accent}77`,
        borderRadius: 8,
        background: `${accent}08`,
        pointerEvents: 'none',
        boxSizing: 'border-box',
        ...(data.revealBacking ? { '--rf-box-delay': `${data.revealBoxDelayMs ?? 0}ms` } : {}),
      }}
    />
  )
}
