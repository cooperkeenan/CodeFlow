import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Box, Button, Chip, CircularProgress, Stack, Typography } from '@mui/material'
import { useEndpointDetail } from '../hooks/useEndpointDetail'
import { endpointDetailFixtureUrl } from '../api/endpoints'
import { flowQueryFn, flowQueryKey } from '../api/queries'
import ContractPanel from '../components/endpoint/ContractPanel'
import KeyMethodPanel from '../components/endpoint/KeyMethodPanel'

const MONO = "'IBM Plex Mono', monospace"

export default function EndpointPage({ repo, fixture, flowPath = '/flow', onBack }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [params] = useSearchParams()
  const entry = params.get('entry')
  const fixtureUrl = fixture ? endpointDetailFixtureUrl(entry) : null
  const { detail, loading, error } = useEndpointDetail(repo, fixtureUrl, entry)

  const backToList = () => {
    if (onBack) return onBack()
    navigate(fixture ? '/repo-fixture' : '/repo')
  }
  const openDiagram = () => navigate(`${flowPath}?entry=${encodeURIComponent(entry)}`)
  const prefetchDiagram = () => {
    if (fixture || !repo) return
    queryClient.prefetchQuery({
      queryKey: flowQueryKey(repo, null, entry, null),
      queryFn: flowQueryFn(repo, null, entry, null),
    })
  }

  const description = detail?.description || detail?.contract?.summary || ''

  return (
    <Box data-testid="endpoint-page" sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Stack
        component="header"
        direction="row"
        alignItems="center"
        spacing={2}
        sx={{ px: 2.5, py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}
      >
        <button className="back" onClick={backToList}>← endpoints</button>
        {detail && (
          <>
            <Chip label={detail.method} size="small" color="primary" />
            <Typography sx={{ fontFamily: MONO, fontSize: 13 }}>{detail.path}</Typography>
            <Typography sx={{ fontFamily: MONO, fontSize: '1.1rem', fontWeight: 600 }}>
              {detail.title}
            </Typography>
          </>
        )}
      </Stack>

      {loading && (
        <Box sx={{ flex: 1, display: 'grid', placeItems: 'center' }}>
          <CircularProgress color="primary" />
        </Box>
      )}
      {error && (
        <Typography className="error" sx={{ p: 3 }}>failed to load endpoint: {error}</Typography>
      )}
      {!loading && !error && !detail && (
        <Typography color="text.secondary" sx={{ p: 3 }}>endpoint not found.</Typography>
      )}

      {detail && (
        <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto', p: 4 }}>
          <Stack spacing={4} sx={{ maxWidth: 720 }}>
            {description && <Typography color="text.secondary">{description}</Typography>}
            <Button
              variant="contained"
              data-testid="view-diagram"
              onClick={openDiagram}
              onMouseEnter={prefetchDiagram}
              onFocus={prefetchDiagram}
              sx={{ alignSelf: 'flex-start' }}
            >
              view diagram
            </Button>
            <ContractPanel contract={detail.contract} />
            <KeyMethodPanel methods={detail.methods} sources={detail.sources} />
          </Stack>
        </Box>
      )}
    </Box>
  )
}
