import NodeBadges from './NodeBadges'
import { LABEL_STYLE, CHIP_STYLE } from './styles'

export default function NodeChrome({ data, align = 'flex-start' }) {
  const foldedTitle = data.foldedArms?.length
    ? data.foldedArms.join(', ')
    : `${data.foldedCount ?? ''} folded`
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: align, width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 5, width: '100%', justifyContent: align === 'center' ? 'center' : 'space-between' }}>
        <span style={LABEL_STYLE}>{data.label}</span>
        {data.chip && (
          <span title={foldedTitle} style={CHIP_STYLE}>{data.chip}</span>
        )}
      </div>
      <NodeBadges badges={data.badges} guardSource={data.guardSource} />
    </div>
  )
}
