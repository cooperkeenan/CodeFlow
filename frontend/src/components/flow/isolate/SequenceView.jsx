import { MONO, SURFACE_2, BORDER, TEXT, TEXT_MUTED, KIND_ACCENT } from '../styles'

const ROOT_STYLE = {
  background: SURFACE_2,
  border: `1px solid ${BORDER}`,
  borderRadius: 3,
  height: '100%',
  minHeight: 0,
  overflow: 'auto',
  padding: 10,
}

const CALLER_STYLE = {
  fontFamily: MONO,
  fontSize: 11,
  color: KIND_ACCENT.entry,
  marginTop: 10,
}

const CALL_ROW = { display: 'flex', gap: 8, fontFamily: MONO, fontSize: 10, lineHeight: 1.7 }
const RAIL_STYLE = { color: TEXT_MUTED, flexShrink: 0 }
const LINE_STYLE = { color: TEXT_MUTED, flex: '0 0 58px' }
const TARGET_STYLE = { color: TEXT, wordBreak: 'break-all' }

const EMPTY_STYLE = { fontFamily: MONO, fontSize: 10, color: TEXT_MUTED, padding: 12 }

export default function SequenceView({ sequence }) {
  if (!sequence?.length) {
    return (
      <div data-testid="sequence-view" data-callers="0" style={EMPTY_STYLE}>
        no call sequence recorded for this class — re-run the analysis to capture call order
      </div>
    )
  }
  return (
    <div data-testid="sequence-view" data-callers={sequence.length} className="nowheel" style={ROOT_STYLE}>
      {sequence.map(entry => (
        <div key={entry.caller_fqn || entry.caller} data-caller={entry.caller}>
          <div style={CALLER_STYLE}>{entry.caller}</div>
          {entry.calls.map((call, index) => (
            <div key={`${call.fqn}:${call.line}`} style={CALL_ROW}>
              <span style={RAIL_STYLE}>{index === entry.calls.length - 1 ? '└─' : '├─'}</span>
              <span style={LINE_STYLE}>line {call.line}</span>
              <span style={RAIL_STYLE}>▶</span>
              <span title={call.fqn} style={TARGET_STYLE}>{call.name}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
