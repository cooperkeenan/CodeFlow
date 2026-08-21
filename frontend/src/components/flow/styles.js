export const MONO = 'IBM Plex Mono, monospace'

export const CANVAS = '#0F1218'
export const GRID = '#232A36'

export const KIND_ACCENT = {
  entry: '#39FF14',
  step: '#64B5F6',
  decision: '#FFB84D',
  pipeline: '#FFB84D',
  parallel: '#CE93D8',
  effect: '#4DD0E1',
  outcome: '#9E9E9E',
  card: '#39FF14',
  snippet: '#64B5F6',
}

export const SURFACE = '#232B3A'
export const SURFACE_2 = '#171C25'
export const BORDER = '#374154'
export const TEXT = 'rgba(237,242,249,0.94)'
export const TEXT_MUTED = 'rgba(226,232,240,0.62)'

export const LABEL_STYLE = {
  fontFamily: MONO,
  fontSize: 14,
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
  fontSize: 10.5,
  color: TEXT_MUTED,
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  borderTop: '1px solid rgba(255,255,255,0.08)',
  minWidth: 0,
}

export const CHIP_STYLE = {
  fontFamily: MONO,
  fontSize: 10,
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

const BASE_TRANSITION =
  'border-color 240ms ease, box-shadow 240ms ease, opacity 420ms cubic-bezier(.4,0,.2,1), filter 420ms ease'
const SIZE_TRANSITION =
  ', width 760ms cubic-bezier(.5,0,.2,1), min-height 760ms cubic-bezier(.5,0,.2,1), border-radius 760ms cubic-bezier(.5,0,.2,1)'
const FRAME_SHADOW = '0 24px 48px -16px rgba(0,0,0,0.55), 0 8px 20px -6px rgba(0,0,0,0.4)'

export function shellStyle(
  base,
  accent,
  { selected, highlighted, dashed, isolated, focused, dimmed, adjacent, entering = false, enterDelay = 0 },
) {
  const lit = highlighted || focused
  const ring = lit ? accent : adjacent ? accent + 'AA' : selected ? accent : accent + '66'
  const focusAnim = [
    entering ? `armIn 420ms cubic-bezier(.22,.9,.28,1) ${enterDelay}ms both` : null,
    'nodeSettle 420ms cubic-bezier(.22,.9,.28,1) both',
    'nodeBreathe 2800ms 420ms ease-in-out infinite',
  ].filter(Boolean).join(', ')
  const glow = focused
    ? `0 0 0 4px ${accent}44, 0 0 28px 3px ${accent}55`
    : adjacent ? `0 0 0 2px ${accent}22` : highlighted ? `0 0 0 3px ${accent}33` : null
  const shadows = [glow, isolated ? FRAME_SHADOW : null].filter(Boolean)
  return {
    ...base,
    ...(isolated
      ? { alignItems: 'stretch', justifyContent: 'center', height: base.minHeight, position: 'relative', padding: 0, gap: 0 }
      : {}),
    ...(isolated === 'open' ? { borderRadius: 4 } : {}),
    border: `${lit || selected ? 2 : 1}px ${dashed ? 'dashed' : 'solid'} ${ring}`,
    boxShadow: shadows.length ? shadows.join(', ') : 'none',
    opacity: dimmed ? 0.3 : adjacent ? 0.72 : 1,
    filter: dimmed ? 'saturate(0.4)' : 'none',
    boxSizing: 'border-box',
    cursor: 'pointer',
    willChange: focused ? 'transform' : 'auto',
    animation: focused ? focusAnim : 'none',
    transition: BASE_TRANSITION + SIZE_TRANSITION,
  }
}

export function revealStyle(data, accent) {
  if (!data.justRevealed) return null
  return {
    '--rf-reveal-accent': accent,
    '--rf-outline-delay': `${data.revealOutlineDelayMs ?? 0}ms`,
  }
}
