import ExpandToggle from './ExpandToggle'
import NodeBadges from './NodeBadges'
import { LABEL_STYLE, CHIP_STYLE, PROVENANCE_STYLE, MONO, TEXT_MUTED, scaleText } from './styles'

const SUBTITLE_STYLE = {
  fontFamily: MONO,
  fontSize: 8,
  color: TEXT_MUTED,
  wordBreak: 'break-word',
  display: '-webkit-box',
  WebkitBoxOrient: 'vertical',
  WebkitLineClamp: 2,
  overflow: 'hidden',
}

export default function NodeChrome({ data, align = 'flex-start', subtitle = null }) {
  const scale = data.scale ?? 1
  const foldedTitle = data.foldedArms?.length
    ? data.foldedArms.join(', ')
    : `${data.foldedCount ?? ''} folded`
  const resolvedSubtitle = subtitle ?? data.oneLiner ?? null
  const hasFooter = data.provenance || data.badges?.length > 0
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: align, width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: Math.round(5 * scale), width: '100%', justifyContent: align === 'center' ? 'center' : 'space-between' }}>
        <span title={data.label} style={scaleText(LABEL_STYLE, scale)}>{data.label}</span>
        {data.chip && (
          <span title={foldedTitle} style={scaleText(CHIP_STYLE, scale)}>{data.chip}</span>
        )}
      </div>
      {resolvedSubtitle && <span title={resolvedSubtitle} style={scaleText(SUBTITLE_STYLE, scale)}>{resolvedSubtitle}</span>}
      {hasFooter && (
        <div style={{
          ...scaleText(PROVENANCE_STYLE, scale),
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: Math.round(6 * scale),
          width: '100%',
          marginTop: Math.round(4 * scale),
          paddingTop: Math.round(4 * scale),
        }}>
          <span title={data.provenance} style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', minWidth: 0 }}>
            {data.provenance}
          </span>
          <NodeBadges badges={data.badges} guardSource={data.guardSource} scale={scale} />
        </div>
      )}
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
