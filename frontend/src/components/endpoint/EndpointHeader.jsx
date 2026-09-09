import { Button, Chip, Stack, Typography } from '@mui/material'
import { methodChipSx } from './contractChips'

const MONO = "'IBM Plex Mono', monospace"

export default function EndpointHeader({ detail, railOpen, onToggleRail, onBack }) {
  return (
    <Stack
      component="header"
      direction="row"
      alignItems="center"
      spacing={2}
      sx={{ px: 2.5, py: 1.5, borderBottom: '1px solid', borderColor: 'var(--area-rim)' }}
    >
      <button className="back" onClick={onBack}>← endpoints</button>
      <Button
        size="small"
        variant="outlined"
        color="inherit"
        data-testid="toggle-rail"
        onClick={onToggleRail}
        sx={{ fontFamily: MONO, fontSize: 11, color: 'text.secondary', borderColor: 'divider' }}
      >
        {railOpen ? 'hide list' : 'show list'}
      </Button>
      {detail && (
        <>
          {detail.method && (
            <Chip
              label={detail.method}
              size="small"
              variant="outlined"
              sx={methodChipSx(detail.method)}
            />
          )}
          <Typography sx={{ fontFamily: MONO, fontSize: 13 }}>{detail.path}</Typography>
          <Typography sx={{ fontFamily: MONO, fontSize: '1.1rem', fontWeight: 600 }}>
            {detail.title}
          </Typography>
        </>
      )}
    </Stack>
  )
}
