import { useNavigate } from 'react-router-dom'
import { Box, CircularProgress, Stack, Typography } from '@mui/material'
import { useRepoHome } from '../hooks/useRepoHome'
import EndpointList from '../components/repo/EndpointList'
import RepoOverview from '../components/repo/RepoOverview'

const MONO = "'IBM Plex Mono', monospace"

export default function RepoHomePage({ repo, fixture, onBack, flowPath = '/flow' }) {
  const { home, loading, error } = useRepoHome(repo, fixture)
  const navigate = useNavigate()
  const openEndpoint = id => navigate(`${flowPath}?entry=${encodeURIComponent(id)}`)

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Stack
        component="header"
        direction="row"
        alignItems="center"
        spacing={2}
        sx={{ px: 2.5, py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}
      >
        {onBack && <button className="back" onClick={onBack}>← repos</button>}
        <Typography sx={{ fontFamily: MONO, fontSize: '1.1rem', fontWeight: 600 }}>
          {home?.title ?? repo ?? 'repo'}
        </Typography>
      </Stack>

      {loading && (
        <Box sx={{ flex: 1, display: 'grid', placeItems: 'center' }}>
          <CircularProgress color="primary" />
        </Box>
      )}
      {error && (
        <Typography className="error" sx={{ p: 3 }}>failed to load repo: {error}</Typography>
      )}
      {home && (
        <Box sx={{ flex: 1, minHeight: 0, display: 'flex' }}>
          <Box
            sx={{
              width: 320,
              flexShrink: 0,
              overflowY: 'auto',
              borderRight: '1px solid',
              borderColor: 'divider',
            }}
          >
            <EndpointList endpoints={home.endpoints} onOpen={openEndpoint} />
          </Box>
          <Box sx={{ flex: 1, minWidth: 0, overflowY: 'auto', p: 4 }}>
            <RepoOverview home={home} onOpenFullMap={() => navigate(flowPath)} />
          </Box>
        </Box>
      )}
    </Box>
  )
}
