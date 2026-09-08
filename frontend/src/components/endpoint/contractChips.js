import { alpha } from '@mui/material/styles'
import { HUE, METHOD } from '../../design/tokens'

const MONO = "'IBM Plex Mono', monospace"

const STATUS_CLASS = {
  2: HUE.green.base,
  3: HUE.teal.base,
  4: HUE.yellow.base,
  5: HUE.red.base,
}

function outlined(color) {
  return {
    fontFamily: MONO,
    fontWeight: 600,
    letterSpacing: '0.06em',
    color,
    borderColor: alpha(color, 0.5),
    bgcolor: alpha(color, 0.12),
  }
}

export function methodChipSx(method) {
  return outlined(METHOD[String(method || '').toUpperCase()] || METHOD.unknown)
}

export function statusChipSx(status) {
  return outlined(STATUS_CLASS[Math.floor(Number(status) / 100)] || METHOD.unknown)
}
