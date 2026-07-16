import Handles from './Handles'
import { SURFACE } from './styles'

export default function ClippedShape({ width, height, clipPath, accent, selected, highlighted, children }) {
  const active = selected || highlighted
  const borderW = active ? 2.5 : 1.5
  const borderColor = active ? accent : accent + '66'
  return (
    <div style={{ position: 'relative', width, height, cursor: 'pointer' }}>
      <div style={{ position: 'absolute', inset: 0, clipPath, background: borderColor }} />
      <div style={{ position: 'absolute', inset: borderW, clipPath, background: SURFACE }} />
      <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', padding: '0 10px', textAlign: 'center' }}>
        {children}
      </div>
      <Handles />
    </div>
  )
}
