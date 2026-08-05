export const MONO = 'IBM Plex Mono, monospace'

export const KIND_ACCENT = {
  entry: '#39FF14',
  step: '#64B5F6',
  decision: '#FFB84D',
  pipeline: '#FFB84D',
  parallel: '#CE93D8',
  effect: '#4DD0E1',
  outcome: '#9E9E9E',
}

export const SURFACE = '#1A1A1A'
export const SURFACE_2 = '#121212'
export const BORDER = '#242424'
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

export function shellStyle(base, accent, { selected, highlighted, dashed }) {
  const ring = highlighted ? accent : selected ? accent : accent + '66'
  return {
    ...base,
    border: `${highlighted || selected ? 2 : 1}px ${dashed ? 'dashed' : 'solid'} ${ring}`,
    boxShadow: highlighted ? `0 0 0 3px ${accent}33` : 'none',
    boxSizing: 'border-box',
    cursor: 'pointer',
    transition: 'border-color 120ms ease, box-shadow 120ms ease',
  }
}
