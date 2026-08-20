export const MONO = 'IBM Plex Mono, monospace'

export const CANVAS = '#2E2E35'
export const GRID = '#43434E'

export const KIND_ACCENT = {
  entry: '#39FF14',
  step: '#64B5F6',
  decision: '#FFB84D',
  pipeline: '#FFB84D',
  parallel: '#CE93D8',
  effect: '#4DD0E1',
  outcome: '#9E9E9E',
}

export const SURFACE = '#3A3A44'
export const SURFACE_2 = '#24242A'
export const BORDER = '#4C4C58'
export const TEXT = 'rgba(255,255,255,0.87)'
export const TEXT_MUTED = 'rgba(255,255,255,0.5)'

export const LABEL_STYLE = {
  fontFamily: MONO,
  fontSize: 11,
  fontWeight: 600,
  color: TEXT,
  lineHeight: 1.35,
  wordBreak: 'break-word',
  display: '-webkit-box',
  WebkitBoxOrient: 'vertical',
  WebkitLineClamp: 3,
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  minWidth: 0,
}

export const PROVENANCE_STYLE = {
  fontFamily: MONO,
  fontSize: 8,
  color: TEXT_MUTED,
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  borderTop: '1px solid rgba(255,255,255,0.08)',
  minWidth: 0,
}

export const CHIP_STYLE = {
  fontFamily: MONO,
  fontSize: 8,
  fontWeight: 600,
  letterSpacing: '0.06em',
  padding: '1px 4px',
  borderRadius: 2,
  color: TEXT,
  background: 'rgba(255,255,255,0.10)',
  border: '1px solid rgba(255,255,255,0.14)',
  flexShrink: 0,
}

export const EFFECT_ICON = {
  http_out: '🌐',
  database: '🗄',
  llm: '🧠',
  file: '📄',
  queue: '📨',
  email: '✉',
  response: '↩',
}

export const BADGE_GLYPH = {
  loop: { glyph: '⟳', title: 'loop' },
  recursive: { glyph: '⟲', title: 'recursive' },
  guarded: { glyph: '⛨', title: 'guarded' },
  dynamic: { glyph: '⚡', title: 'dynamic dispatch' },
}

export function scaleText(style, scale = 1) {
  if (scale === 1) return style
  return { ...style, fontSize: Math.round(style.fontSize * scale * 10) / 10 }
}

export function scalePad(vertical, horizontal, scale = 1) {
  return `${Math.round(vertical * scale)}px ${Math.round(horizontal * scale)}px`
}

export function shellStyle(
  base, accent, { selected, highlighted, dashed, focused, dimmed, adjacent },
) {
  const lit = highlighted || focused
  const ring = lit ? accent : adjacent ? accent + 'AA' : selected ? accent : accent + '66'
  return {
    ...base,
    border: `${lit || selected ? 2 : 1}px ${dashed ? 'dashed' : 'solid'} ${ring}`,
    boxShadow: focused
      ? `0 0 0 4px ${accent}44, 0 0 28px 3px ${accent}55`
      : adjacent ? `0 0 0 2px ${accent}22` : highlighted ? `0 0 0 3px ${accent}33` : 'none',
    opacity: dimmed ? 0.3 : adjacent ? 0.72 : 1,
    filter: dimmed ? 'saturate(0.4)' : 'none',
    boxSizing: 'border-box',
    cursor: 'pointer',
    willChange: focused ? 'transform' : 'auto',
    animation: focused
      ? 'nodeSettle 420ms cubic-bezier(.22,.9,.28,1) both, nodeBreathe 2800ms 420ms ease-in-out infinite'
      : 'none',
    transition:
      'border-color 240ms ease, box-shadow 240ms ease, opacity 420ms cubic-bezier(.4,0,.2,1), filter 420ms ease',
  }
}
