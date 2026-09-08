export const HUE = {
  blue: { base: '#2899F5', hot: '#7EC2F8', rim: '#116DBF', fill: '#0B2A42' },
  teal: { base: '#3FCBD6', hot: '#8FE5EC', rim: '#0A7C85', fill: '#082C30' },
  purple: { base: '#B4A0FF', hot: '#D4C7FF', rim: '#6E5FB7', fill: '#241F3D' },
  orange: { base: '#FF8C00', hot: '#FFB870', rim: '#A75900', fill: '#3A2000' },
  yellow: { base: '#FFCC00', hot: '#FFE066', rim: '#8A6D00', fill: '#332A00' },
  red: { base: '#F1707B', hot: '#F8A3AA', rim: '#C9313C', fill: '#3D1418' },
  green: { base: '#6BB700', hot: '#A8DC4C', rim: '#477A00', fill: '#1B2E06' },
  grey: { base: '#CCCCCC', hot: '#E6E6E6', rim: '#6E6E6E', fill: '#333333' },
}

export const NEUTRAL = {
  bg: '#1F1F1F',
  surface: '#2D2D2D',
  surfaceSunken: '#252525',
  surface2: '#333333',
  surface3: '#3F3F3F',
  surface4: '#484848',
  surface5: '#565656',
  border: '#3F3F3F',
  borderHi: '#565656',
  canvasBorder: '#484848',
  onAccent: '#04213A',
  onAction: '#132200',
}

export const TEXT = {
  primary: '#E6E6E6',
  secondary: '#C8C6C4',
  disabled: '#8A8886',
  canvas: '#E6E6E6',
  canvasMuted: '#B3B0AD',
}

export const ACCENT = HUE.blue.base
export const ACCENT_HOT = HUE.blue.hot
export const ACCENT_RIM = HUE.blue.rim
export const ACCENT_GLOW = 'rgba(40,153,245,0.28)'
export const LINK = HUE.blue.base
export const ACTION = HUE.green.base

export const KIND = {
  entry: HUE.blue.base,
  step: HUE.teal.base,
  decision: HUE.yellow.base,
  pipeline: HUE.yellow.base,
  loop: HUE.yellow.base,
  parallel: HUE.purple.base,
  effect: HUE.orange.base,
  outcome: HUE.grey.base,
  card: HUE.blue.base,
  snippet: HUE.teal.base,
}

export const STATUS = {
  success: HUE.green.base,
  warning: HUE.yellow.base,
  danger: HUE.red.base,
  info: HUE.blue.base,
  recommend: HUE.green.base,
}

export const METHOD = {
  GET: HUE.green.base,
  HEAD: HUE.green.base,
  POST: HUE.blue.base,
  PUT: HUE.purple.base,
  PATCH: HUE.purple.base,
  OPTIONS: HUE.grey.base,
  DELETE: HUE.red.base,
  unknown: HUE.grey.base,
}

export const EDGE = {
  normal: '#6E6E6E',
  stitch: '#8A8886',
  highlighted: '#FFFFFF',
  flow: HUE.blue.base,
  packet: HUE.blue.hot,
}

export const AREA = {
  explore: HUE.blue,
  maps: HUE.orange,
  tour: HUE.green,
  edit: HUE.purple,
  plain: HUE.grey,
}

export function alphaHex(hex, aa) {
  if (typeof hex !== 'string' || !/^#[0-9A-Fa-f]{6}$/.test(hex)) {
    throw new Error(`alphaHex expects a #RRGGBB literal, got: ${hex}`)
  }
  return `${hex}${aa}`
}

function rampVars() {
  const out = {}
  for (const [name, tone] of Object.entries(HUE)) {
    out[`--${name}`] = tone.base
    out[`--${name}-hot`] = tone.hot
    out[`--${name}-rim`] = tone.rim
    out[`--${name}-fill`] = tone.fill
  }
  return out
}

export const CSS_VARS = {
  ...rampVars(),
  '--bg': NEUTRAL.bg,
  '--surface': NEUTRAL.surface,
  '--surface-2': NEUTRAL.surface2,
  '--surface-3': NEUTRAL.surface3,
  '--surface-4': NEUTRAL.surface4,
  '--surface-5': NEUTRAL.surface5,
  '--border': NEUTRAL.border,
  '--border-hi': NEUTRAL.borderHi,
  '--on-accent': NEUTRAL.onAccent,
  '--on-action': NEUTRAL.onAction,
  '--text': TEXT.primary,
  '--text-medium': TEXT.secondary,
  '--text-disabled': TEXT.disabled,
  '--muted': TEXT.secondary,
  '--accent': ACCENT,
  '--accent-hot': ACCENT_HOT,
  '--accent-rim': ACCENT_RIM,
  '--accent-glow': ACCENT_GLOW,
  '--link': LINK,
  '--action': ACTION,
  '--action-rim': HUE.green.rim,
  '--action-fill': HUE.green.fill,
  '--error': STATUS.danger,
  '--warning': STATUS.warning,
  '--recommend': STATUS.recommend,
  '--info': STATUS.info,
  '--success': STATUS.success,
  '--edge': EDGE.normal,
  '--edge-stitch': EDGE.stitch,
  '--primary-container': HUE.blue.fill,
  '--primary-container-hover': HUE.blue.rim,
}
