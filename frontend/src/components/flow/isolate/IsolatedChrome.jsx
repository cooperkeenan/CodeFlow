import FrameContent from './FrameContent'
import { MONO, TEXT } from '../styles'

const TITLE_STYLE = {
  display: 'block',
  fontFamily: MONO,
  fontSize: 18,
  fontWeight: 600,
  color: TEXT,
  lineHeight: 1.3,
  textAlign: 'center',
  wordBreak: 'break-word',
  padding: '2px 44px 0',
  flexShrink: 0,
}

const CLOSE_STYLE = {
  position: 'absolute',
  top: 0,
  right: 0,
  width: 24,
  height: 24,
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: 17,
  lineHeight: 1,
  color: TEXT,
  cursor: 'pointer',
  userSelect: 'none',
  borderRadius: 3,
}

const BODY_STYLE = {
  flex: 1,
  minHeight: 0,
  overflow: 'hidden',
  marginTop: 14,
  padding: '0 6px',
}

export default function IsolatedChrome({ data }) {
  const scale = data.frameScale ?? 1
  const from = (data.frameFrom ?? 1) * scale
  const to = (data.frameTo ?? 1) * scale
  const growing = data.frameGrowing
  return (
    <div
      style={{
        position: 'relative',
        alignSelf: 'stretch',
        flexGrow: 1,
        minWidth: 0,
        height: '100%',
        overflow: 'hidden',
      }}
    >
      <span
        role="button"
        title="close isolation"
        className="nodrag nopan"
        data-testid="isolate-close"
        style={{
          ...CLOSE_STYLE,
          top: Math.round(2 * scale),
          right: Math.round(2 * scale),
          width: Math.round(24 * scale),
          height: Math.round(24 * scale),
          fontSize: Math.round(17 * scale),
          opacity: data.isolated === 'closing' ? 0 : 1,
          transition: 'opacity 220ms ease',
          zIndex: 2,
        }}
        onPointerDown={event => {
          event.stopPropagation()
          event.preventDefault()
          data.onIsolate?.(data.nodeId)
        }}
        onClick={event => {
          event.stopPropagation()
          event.preventDefault()
        }}
      >
        ×
      </span>
      <div
        className={growing ? 'rf-frame-grow' : undefined}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: Math.round((data.frameWidth ?? 0) / scale) || `${100 / scale}%`,
          height: Math.round((data.frameHeight ?? 0) / scale) || `${100 / scale}%`,
          transform: `scale(${to})`,
          transformOrigin: 'top left',
          '--rf-from': from,
          '--rf-to': to,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <span title={data.label} style={TITLE_STYLE}>{data.label}</span>
        <div
          className="nowheel"
          style={{
            ...BODY_STYLE,
            opacity: data.isolated === 'closing' ? 0 : 1,
            transition: 'opacity 220ms ease',
          }}
        >
          <FrameContent
            repo={data.repo}
            nodeId={data.nodeId}
            provenance={data.provenance}
            collapsed={data.isolated === 'closing'}
            ready={data.frameReady}
          />
        </div>
      </div>
    </div>
  )
}
