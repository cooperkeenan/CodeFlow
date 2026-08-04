import ExpandToggle from './ExpandToggle'
import NodeBadges from './NodeBadges'
import { LABEL_STYLE, CHIP_STYLE, MONO, TEXT_MUTED, scaleText } from './styles'

const SUBTITLE_STYLE = {
  fontFamily: MONO,
  fontSize: 8,
  color: TEXT_MUTED,
  wordBreak: 'break-all',
  display: '-webkit-box',
  WebkitBoxOrient: 'vertical',
  WebkitLineClamp: 1,
  overflow: 'hidden',
}

export default function NodeChrome({ data, align = 'flex-start', subtitle = null }) {
  const scale = data.scale ?? 1
  const foldedTitle = data.foldedArms?.length
    ? data.foldedArms.join(', ')
    : `${data.foldedCount ?? ''} folded`
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: align, width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: Math.round(5 * scale), width: '100%', justifyContent: align === 'center' ? 'center' : 'space-between' }}>
        <span title={data.label} style={scaleText(LABEL_STYLE, scale)}>{data.label}</span>
        {data.chip && (
          <span title={foldedTitle} style={scaleText(CHIP_STYLE, scale)}>{data.chip}</span>
        )}
      </div>
      {subtitle && <span title={subtitle} style={scaleText(SUBTITLE_STYLE, scale)}>{subtitle}</span>}
      <NodeBadges badges={data.badges} guardSource={data.guardSource} scale={scale} />
      {data.expandable && (
        <div style={{ marginTop: Math.round(4 * scale) }}>
          <ExpandToggle
            expanded={data.expanded}
            count={data.hiddenCount}
            onToggle={data.onToggle}
            nodeId={data.nodeId}
            scale={scale}
          />
        </div>
      )}
    </div>
  )
}
