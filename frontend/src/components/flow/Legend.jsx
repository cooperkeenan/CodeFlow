import { useState } from 'react'
import { MONO, SURFACE_2, BORDER, TEXT, TEXT_MUTED, KIND_ACCENT } from './styles'

const ROW = { display: 'flex', alignItems: 'center', gap: 8, fontFamily: MONO, fontSize: 10, color: TEXT_MUTED }
const SWATCH = { width: 14, textAlign: 'center', color: TEXT, flexShrink: 0 }
const HEAD = { fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.32)', margin: '8px 0 3px' }

const SHAPES = [
  ['⬭', 'entry', KIND_ACCENT.entry],
  ['▭', 'step', KIND_ACCENT.step],
  ['▌◇', 'decision', KIND_ACCENT.decision],
  ['●', 'pipeline step', KIND_ACCENT.pipeline],
  ['⑃', 'parallel split', KIND_ACCENT.parallel],
  ['◆', 'effect', KIND_ACCENT.effect],
  ['●', 'outcome', KIND_ACCENT.outcome],
]
const EDGES = [
  ['tree (solid)', '━'],
  ['cross-link (faded)', '─'],
  ['except / dynamic (dashed)', '╌'],
  ['stitch (gutter)', '┈'],
]
const BADGES = [['⟳', 'loop'], ['⟲', 'recursive'], ['⛨', 'guarded'], ['⚡', 'dynamic']]

export default function Legend() {
  const [open, setOpen] = useState(false)
  return (
    <div style={{
      position: 'absolute', bottom: 12, left: 12, zIndex: 5,
      background: SURFACE_2, border: `1px solid ${BORDER}`, borderRadius: 4,
      padding: open ? '8px 12px 12px' : '6px 12px', width: open ? 210 : 'auto',
    }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{ background: 'none', border: 'none', color: TEXT, fontFamily: MONO, fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', cursor: 'pointer', padding: 0 }}
      >
        {open ? '▾ legend' : '▸ legend'}
      </button>
      {open && (
        <>
          <div style={HEAD}>shapes</div>
          {SHAPES.map(([g, name, color]) => (
            <div key={name} style={ROW}><span style={{ ...SWATCH, color }}>{g}</span>{name}</div>
          ))}
          <div style={HEAD}>edges</div>
          {EDGES.map(([name, g]) => (
            <div key={name} style={ROW}><span style={SWATCH}>{g}</span>{name}</div>
          ))}
          <div style={HEAD}>badges</div>
          {BADGES.map(([g, name]) => (
            <div key={name} style={ROW}><span style={SWATCH}>{g}</span>{name}</div>
          ))}
          <div style={HEAD}>confidence</div>
          <div style={ROW}><span style={SWATCH}>◐</span>inferred = 60% opacity</div>
          <div style={ROW}><span style={SWATCH}>⚡</span>dynamic = dashed</div>
        </>
      )}
    </div>
  )
}
