import { Box, Stack, Typography } from '@mui/material'
import { ACTION, NEUTRAL, STATUS, TEXT } from '../../design/tokens'

const DOT = {
  done: ACTION,
  active: STATUS.info,
  failed: STATUS.danger,
  pending: NEUTRAL.surface5,
}

const LABEL = {
  done: TEXT.secondary,
  active: TEXT.primary,
  failed: STATUS.danger,
  pending: TEXT.disabled,
}

export default function RunPhases({ phases = [] }) {
  return (
    <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1, flexWrap: 'wrap' }}>
      {phases.map((phase, index) => (
        <Stack key={phase.key} direction="row" alignItems="center" spacing={1}>
          {index > 0 && (
            <Box sx={{ width: 12, height: '1px', backgroundColor: NEUTRAL.border }} />
          )}
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: DOT[phase.state] ?? DOT.pending,
              boxShadow: phase.state === 'active' ? `0 0 0 3px ${NEUTRAL.surface3}` : 'none',
            }}
          />
          <Typography
            variant="caption"
            sx={{
              fontFamily: "'IBM Plex Mono', monospace",
              color: LABEL[phase.state] ?? LABEL.pending,
              fontWeight: phase.state === 'active' ? 600 : 400,
            }}
          >
            {phase.label}
          </Typography>
        </Stack>
      ))}
    </Stack>
  )
}
