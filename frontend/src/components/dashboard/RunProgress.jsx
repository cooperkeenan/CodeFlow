import { useEffect, useState } from 'react'
import { Alert, AlertTitle, Box, Button, Paper, Stack, Typography } from '@mui/material'
import TerminalIcon from '@mui/icons-material/Terminal'
import RunLogTerminal from './RunLogTerminal'
import RunPhases from './RunPhases'
import RunProgressBar from './RunProgressBar'
import { NEUTRAL, TEXT } from '../../design/tokens'

function clock(seconds) {
  const whole = Math.max(0, Math.round(seconds ?? 0))
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, '0')}`
}

function phaseLabel(progress) {
  const phase = (progress?.phases ?? []).find(p => p.state === 'active' || p.state === 'failed')
  return phase?.label ?? progress?.stage_label ?? ''
}

export default function RunProgress({ progress, events, error }) {
  const [showLog, setShowLog] = useState(false)
  const failed = Boolean(error)
  const repo = progress?.repo

  useEffect(() => {
    if (failed) setShowLog(true)
  }, [failed])

  return (
    <Paper sx={{ p: 2, mb: 2, backgroundColor: NEUTRAL.surfaceSunken }}>
      <Stack direction="row" alignItems="baseline" justifyContent="space-between" sx={{ mb: 1 }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'IBM Plex Mono', monospace" }}>
          {failed ? 'failed' : phaseLabel(progress) || 'starting'}
          {repo ? ` · ${repo}` : ''}
        </Typography>
        <Typography variant="caption" sx={{ color: TEXT.disabled, fontFamily: "'IBM Plex Mono', monospace" }}>
          {clock(progress?.elapsed)} · {progress?.percent ?? 0}%
        </Typography>
      </Stack>

      <RunPhases phases={progress?.phases ?? []} />
      <RunProgressBar
        percent={progress?.percent ?? 0}
        ceiling={progress?.percent_ceiling ?? 0}
        points={progress?.points ?? []}
        failed={failed}
      />

      {!failed && (
        <Typography
          variant="caption"
          component="div"
          data-testid="progress-detail"
          sx={{ color: TEXT.disabled, fontFamily: "'IBM Plex Mono', monospace", minHeight: 18 }}
        >
          {progress?.detail || 'waiting for the next step…'}
        </Typography>
      )}

      {failed && (
        <Alert severity="error" sx={{ mt: 1 }} data-testid="run-error">
          <AlertTitle sx={{ fontFamily: "'IBM Plex Mono', monospace" }}>
            failed during {progress?.failed_stage ?? 'analysis'}
          </AlertTitle>
          <Box sx={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 12, wordBreak: 'break-word' }}>
            {error}
          </Box>
        </Alert>
      )}

      <Button
        size="small"
        startIcon={<TerminalIcon fontSize="small" />}
        onClick={() => setShowLog(open => !open)}
        sx={{ mt: 1, color: TEXT.secondary, px: 0.5 }}
      >
        {showLog ? 'hide log' : `show log (${events.length})`}
      </Button>
      {showLog && <RunLogTerminal events={events} />}
    </Paper>
  )
}
