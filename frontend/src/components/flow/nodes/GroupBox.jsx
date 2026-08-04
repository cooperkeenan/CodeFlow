import { KIND_ACCENT } from '../styles'

export default function GroupBox({ data }) {
  const accent = KIND_ACCENT[data.ownerKind] ?? KIND_ACCENT.decision
  return (
    <div
      style={{
        width: data.width,
        height: data.height,
        border: `1px dashed ${accent}`,
        borderRadius: 6,
        background: `${accent}0A`,
        pointerEvents: 'none',
        boxSizing: 'border-box',
      }}
    />
  )
}
