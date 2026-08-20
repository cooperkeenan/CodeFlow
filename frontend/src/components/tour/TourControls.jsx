import { MONO, SURFACE_2, BORDER, TEXT, TEXT_MUTED, KIND_ACCENT } from '../flow/styles'
import { STEP_MS } from '../../hooks/useTourPlayback'

const RING = 56.5

function ProgressRing({ index, playing }) {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" style={{ flexShrink: 0 }}>
      <circle cx="11" cy="11" r="9" fill="none" stroke="#2a2a2a" strokeWidth="2" />
      <circle
        key={index}
        cx="11" cy="11" r="9" fill="none" stroke={KIND_ACCENT.entry} strokeWidth="2"
        strokeDasharray={RING} strokeDashoffset={RING} strokeLinecap="round"
        transform="rotate(-90 11 11)"
        style={{
          animation: `ringSweep ${STEP_MS}ms linear forwards`,
          animationPlayState: playing ? 'running' : 'paused',
        }}
      />
    </svg>
  )
}

const BTN = {
  fontFamily: MONO, fontSize: 12, color: TEXT, background: 'transparent',
  border: `1px solid ${BORDER}`, borderRadius: 3, padding: '5px 11px', cursor: 'pointer',
  lineHeight: 1.2,
}

export default function TourControls({ index, count, playing, onPrev, onNext, onToggle, onRestart, onGoto }) {
  const atEnd = index >= count - 1
  return (
    <div
      style={{
        position: 'absolute', bottom: 16, left: 24, zIndex: 9,
        display: 'flex', alignItems: 'center', gap: 12, background: SURFACE_2,
        border: `1px solid ${BORDER}`, borderRadius: 4, padding: '9px 14px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
      }}
    >
      <ProgressRing index={index} playing={playing} />
      <button style={BTN} onClick={onPrev} disabled={index === 0} title="previous (left arrow)">
        {'‹'}
      </button>
      <button style={{ ...BTN, minWidth: 78 }} onClick={atEnd ? onRestart : onToggle} title="play / pause (space)">
        {atEnd ? 'replay' : playing ? '‖ pause' : '▶ play'}
      </button>
      <button style={BTN} onClick={onNext} disabled={atEnd} title="next (right arrow)">
        {'›'}
      </button>
      <div style={{ display: 'flex', gap: 3, alignItems: 'center' }}>
        {Array.from({ length: count }, (_, i) => (
          <button
            key={i}
            onClick={() => onGoto(i)}
            title={`step ${i + 1}`}
            style={{
              width: i === index ? 20 : 8, height: 4, borderRadius: 2, border: 'none', padding: 0,
              cursor: 'pointer', transition: 'width 220ms ease, background 220ms ease',
              background: i === index ? KIND_ACCENT.entry : i < index ? '#4a4a4a' : '#2a2a2a',
            }}
          />
        ))}
      </div>
      <span style={{ fontFamily: MONO, fontSize: 11, color: TEXT_MUTED, minWidth: 44, textAlign: 'right' }}>
        {index + 1} / {count}
      </span>
    </div>
  )
}
