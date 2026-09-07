import { alpha } from '@mui/material/styles'

const MONO = "'IBM Plex Mono', monospace"

const METHOD_COLORS = {
  GET: '#64B5F6',
  HEAD: '#64B5F6',
  POST: '#FFB84D',
  PUT: '#B39DDB',
  PATCH: '#B39DDB',
  OPTIONS: '#B39DDB',
  DELETE: '#FF6B6B',
}
const UNKNOWN_METHOD = '#9E9E9E'
const OK_STATUS = '#4DD0C7'
const OTHER_STATUS = '#9E9E9E'

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
  return outlined(METHOD_COLORS[String(method || '').toUpperCase()] || UNKNOWN_METHOD)
}

export function statusChipSx(status) {
  return outlined(String(status).startsWith('2') ? OK_STATUS : OTHER_STATUS)
}
