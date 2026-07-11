import { useEffect, useState } from 'react'
import { Alert, Box, Button, Chip, Paper, Stack, Typography } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import { getRepoMap, listRepoMaps } from '../../api/repomaps'
import { runLocalCi } from '../../api/ci'

export default function RepoMapsPanel({ onOpenMap }) {
  const [maps, setMaps] = useState([])
  const [error, setError] = useState(null)
  const [running, setRunning] = useState(false)

  const refresh = () => listRepoMaps().then(d => setMaps(d.repo_maps)).catch(e => setError(e.message))
  useEffect(() => { refresh() }, [])

  const open = (repo) => getRepoMap(repo).then(d => onOpenMap(d.map)).catch(e => setError(e.message))

  const runCi = () => {
    setError(null)
    setRunning(true)
    runLocalCi()
      .then(refresh)
      .catch(e => setError(e.message))
      .finally(() => setRunning(false))
  }

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
        <Typography variant="h6">Repo Maps</Typography>
        <Button variant="contained" startIcon={<PlayArrowIcon />} onClick={runCi} disabled={running}>
          {running ? 'Running…' : 'Run Local CI'}
        </Button>
      </Stack>
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
