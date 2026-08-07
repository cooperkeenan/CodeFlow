import { MONO, BORDER, TEXT, TEXT_MUTED } from '../styles'

const ROW_STYLE = { display: 'flex', justifyContent: 'flex-end', gap: 4, marginBottom: 6 }

function buttonStyle(active) {
  return {
    fontFamily: MONO,
    fontSize: 11,
    lineHeight: '16px',
    padding: '0 6px',
    borderRadius: 2,
    border: `1px solid ${active ? TEXT_MUTED : BORDER}`,
    color: active ? TEXT : TEXT_MUTED,
    background: active ? 'rgba(255,255,255,0.08)' : 'transparent',
    cursor: 'pointer',
    userSelect: 'none',
  }
}

export default function ViewToggle({ mode, onChange }) {
  const pick = next => event => {
    event.stopPropagation()
    event.preventDefault()
    onChange(next)
  }
  const stop = event => {
    event.stopPropagation()
    event.preventDefault()
  }
  return (
    <div style={ROW_STYLE}>
      <span
        role="button"
        title="code"
        className="nodrag nopan"
        data-testid="view-code"
        data-active={mode === 'code'}
        style={buttonStyle(mode === 'code')}
        onPointerDown={pick('code')}
        onClick={stop}
      >
        {'</>'}
      </span>
      <span
        role="button"
        title="sequence diagram"
        className="nodrag nopan"
        data-testid="view-sequence"
        data-active={mode === 'sequence'}
        style={buttonStyle(mode === 'sequence')}
        onPointerDown={pick('sequence')}
        onClick={stop}
      >
        ⇄
      </span>
    </div>
  )
}
