import { useEffect, useRef } from 'react'
import { Box } from '@mui/material'
import { ACTION, NEUTRAL, STATUS, TEXT } from '../../design/tokens'

const LEVEL = {
  stage: { glyph: '▸', colour: TEXT.primary, weight: 600 },
  step: { glyph: ' ', colour: TEXT.disabled, weight: 400 },
  done: { glyph: '✓', colour: ACTION, weight: 400 },
  warn: { glyph: '!', colour: STATUS.warning, weight: 400 },
  error: { glyph: '✗', colour: STATUS.danger, weight: 600 },
}

const clockOf = (ts) =>
  new Date(ts * 1000).toLocaleTimeString([], { hour12: false })

export default function RunLogTerminal({ events = [], maxHeight = 220 }) {
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'nearest' })
  }, [events.length])

  return (
    <Box
      data-testid="run-log-terminal"
      sx={{
        mt: 1,
        p: 1,
        maxHeight,
        overflowY: 'auto',
        backgroundColor: NEUTRAL.bg,
        border: `1px solid ${NEUTRAL.border}`,
        borderRadius: 0.5,
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 11,
        lineHeight: 1.6,
      }}
    >
      {events.length === 0 && (
        <Box sx={{ color: TEXT.disabled }}>waiting for the first log line…</Box>
      )}
      {events.map(event => {
        const style = LEVEL[event.level] ?? LEVEL.step
        return (
          <Box key={event.seq} sx={{ display: 'flex', gap: 1, whiteSpace: 'pre-wrap' }}>
            <Box component="span" sx={{ color: NEUTRAL.surface5, flexShrink: 0 }}>
              {clockOf(event.ts)}
            </Box>
            <Box component="span" sx={{ color: style.colour, flexShrink: 0, width: 10 }}>
              {style.glyph}
            </Box>
            <Box component="span" sx={{ color: style.colour, fontWeight: style.weight }}>
              {event.message}
            </Box>
          </Box>
        )
      })}
      <div ref={endRef} />
    </Box>
  )
}
