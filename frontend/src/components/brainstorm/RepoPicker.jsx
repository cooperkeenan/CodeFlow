import { Box, Button, Typography } from '@mui/material'
import { useRepoMaps } from '../../hooks/RepoMapsContext'

const MONO = "'IBM Plex Mono', monospace"

export default function RepoPicker({ onPick }) {
  const { maps } = useRepoMaps()
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>Choose a repo to brainstorm</Typography>
      {maps.length === 0 && (
        <Typography sx={{ fontFamily: MONO, fontSize: 13, color: 'text.disabled' }}>
          No repo maps yet.
        </Typography>
      )}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, alignItems: 'flex-start' }}>
        {maps.map(m => (
          <Button key={m.repo} variant="outlined" onClick={() => onPick(m.repo)} sx={{ fontFamily: MONO }}>
            {m.repo}
          </Button>
        ))}
      </Box>
    </Box>
  )
}
