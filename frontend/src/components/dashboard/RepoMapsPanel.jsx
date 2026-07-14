import { useEffect, useState } from 'react'
import { Alert, Box, Button, Chip, LinearProgress, Paper, Stack, Typography } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import { getRepoMap, listRepoMaps } from '../../api/repomaps'
import { getProgress, runLocalCi } from '../../api/ci'

export default function RepoMapsPanel({ onOpenMap }) {
  const [maps, setMaps] = useState([])
  const [error, setError] = useState(null)
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(null)

  const refresh = () => listRepoMaps().then(d => setMaps(d.repo_maps)).catch(e => setError(e.message))
  useEffect(() => { refresh() }, [])

  const open = (repo) => getRepoMap(repo).then(d => onOpenMap(d.map)).catch(e => setError(e.message))

  const runCi = async () => {
    setError(null)
    setProgress(null)
    setRunning(true)
    try {
      const res = await runLocalCi()
      if (res && res.started === false) {
        setError('An analysis is already running')
        setRunning(false)
        return
      }
    } catch (e) {
      setError(e.message)
      setRunning(false)
      return
    }
    const timer = setInterval(async () => {
      try {
        const p = await getProgress()
        setProgress(p)
        if (!p.active) {
          clearInterval(timer)
          setRunning(false)
          setProgress(null)
          if (p.error) setError(p.error)
          else refresh()
        }
      } catch {
        /* transient poll failure — keep polling */
      }
    }, 1500)
  }

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
        <Typography variant="h6">Repo Maps</Typography>
        <Button variant="contained" startIcon={<PlayArrowIcon />} onClick={runCi} disabled={running}>
          {running ? 'Running…' : 'Run Local CI'}
        </Button>
      </Stack>
      {running && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress variant="determinate" value={progress?.percent ?? 0} sx={{ mb: 0.5 }} />
          <Typography variant="caption" color="text.secondary">
            {progress ? `${progress.current} — ${progress.percent}%` : 'starting…'}
          </Typography>
        </Box>
      )}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
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
    </Box>
  )
}
