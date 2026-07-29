import { useState } from 'react'
import { Alert, Box, Button, Chip, LinearProgress, Paper, Stack, Typography } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import GitHubIcon from '@mui/icons-material/GitHub'
import { getRepoMap } from '../../api/repomaps'
import { useRepoMaps } from '../../hooks/RepoMapsContext'
import { useCiProgress } from '../../hooks/useCiProgress'
import GithubRepoPicker from './GithubRepoPicker'

export default function RepoMapsPanel({ onOpenMap }) {
  const { maps, error: listError, refresh } = useRepoMaps()
  const { running, progress, error, setError, startRun, startGithubRun } = useCiProgress(refresh)
  const [pickerOpen, setPickerOpen] = useState(false)
  const [openError, setOpenError] = useState(null)

  const open = (repo) => getRepoMap(repo).then(d => onOpenMap(d.map)).catch(e => setOpenError(e.message))

  const onGithubClick = () => {
    setError(null)
    setOpenError(null)
    setPickerOpen(true)
  }

  const onPickRepo = (fullName) => {
    setPickerOpen(false)
    startGithubRun(fullName)
  }

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
        <Typography variant="h6">Repo Maps</Typography>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" startIcon={<GitHubIcon />} onClick={onGithubClick} disabled={running}>
            Select GitHub Repo
          </Button>
          <Button variant="contained" startIcon={<PlayArrowIcon />} onClick={startRun} disabled={running}>
            {running ? 'Running…' : 'Run Local CI'}
          </Button>
        </Stack>
      </Stack>
      {running && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress variant="determinate" value={progress?.percent ?? 0} sx={{ mb: 0.5 }} />
          <Typography variant="caption" color="text.secondary">
            {progress ? `${progress.current} — ${progress.percent}%` : 'starting…'}
          </Typography>
        </Box>
      )}
      {(error || openError || listError) && (
        <Alert severity="error" sx={{ mb: 2 }}>{error || openError || listError}</Alert>
      )}
      {maps.length === 0 && <Typography color="text.secondary">No saved RepoMaps yet. Run Local CI to generate one.</Typography>}
      <Stack spacing={1}>
        {maps.map(m => (
          <Paper
            key={m.repo}
            onClick={() => open(m.repo)}
            sx={{ p: 2, cursor: 'pointer', '&:hover': { borderColor: 'primary.main' } }}
          >
            <Stack direction="row" alignItems="center" spacing={1}>
              <Chip label={m.source} size="small" color="primary" variant="outlined" />
              <Typography sx={{ fontFamily: "'IBM Plex Mono', monospace", flexGrow: 1 }}>{m.repo}</Typography>
              <Typography variant="caption" color="text.secondary">
                updated {new Date(m.updated_at).toLocaleString()}
              </Typography>
            </Stack>
          </Paper>
        ))}
      </Stack>
      <GithubRepoPicker open={pickerOpen} onClose={() => setPickerOpen(false)} onSelect={onPickRepo} />
    </Box>
  )
}
