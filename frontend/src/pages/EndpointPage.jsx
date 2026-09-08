import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Box, Chip, CircularProgress, Stack, Typography } from '@mui/material'
import { useEndpointDetail } from '../hooks/useEndpointDetail'
import { useRepoHome } from '../hooks/useRepoHome'
import EndpointList from '../components/repo/EndpointList'
import { endpointDetailFixtureUrl } from '../api/endpoints'
import { flowQueryFn, flowQueryKey } from '../api/queries'
import ContractPanel from '../components/endpoint/ContractPanel'
import { methodChipSx } from '../components/endpoint/contractChips'
import KeyMethodPanel from '../components/endpoint/KeyMethodPanel'
import EndpointDiagramPane from '../components/endpoint/EndpointDiagramPane'

const MONO = "'IBM Plex Mono', monospace"
const REPO_HOME_FIXTURE = '/fixture/repo_home.json'

export default function EndpointPage({ repo, fixture, flowPath = '/flow', onBack }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [params, setParams] = useSearchParams()
  const entry = params.get('entry')
  const fixtureUrl = fixture ? endpointDetailFixtureUrl(entry) : null
  const { detail, loading, error } = useEndpointDetail(repo, fixtureUrl, entry)
  const { home } = useRepoHome(repo, fixture ? REPO_HOME_FIXTURE : null)
  const [selectedRoute, setSelectedRoute] = useState(null)
  useEffect(() => { setSelectedRoute(null) }, [entry])
  const selectEndpoint = id => setParams({ entry: id })

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

  const contracts = detail?.contracts ?? (detail?.contract ? [detail.contract] : [])
  const description = detail?.description || contracts[0]?.summary || ''
  const selectedContract = contracts.find(c => `${c.method}:${c.path}` === selectedRoute) ?? null

  return (
    <Box data-testid="endpoint-page" className="area-rail" sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Stack
        component="header"
        direction="row"
        alignItems="center"
        spacing={2}
        sx={{ px: 2.5, py: 1.5, borderBottom: '1px solid', borderColor: 'var(--area-rim)' }}
      >
        <button className="back" onClick={backToList}>← endpoints</button>
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

      <Box sx={{ flex: 1, minHeight: 0, display: 'flex' }}>
        {home?.endpoints?.length > 0 && (
          <Box
            sx={{
              width: 320,
              flexShrink: 0,
              overflowY: 'auto',
              borderRight: '1px solid',
              borderColor: 'divider',
            }}
          >
            <EndpointList
              endpoints={home.endpoints}
              onOpen={selectEndpoint}
              repo={repo}
              canPrefetch={!fixture}
              activeId={entry}
              onOverview={backToList}
            />
          </Box>
        )}

        <Box
          sx={{
            flex: '0 1 760px',
            minWidth: 0,
            overflowY: 'auto',
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            '&::-webkit-scrollbar': { display: 'none' },
          }}
        >
          {loading && (
            <Box sx={{ height: '100%', display: 'grid', placeItems: 'center' }}>
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
            <Stack spacing={4} sx={{ maxWidth: 720, p: 4 }}>
              {description && <Typography color="text.secondary">{description}</Typography>}
              <ContractPanel
                contracts={contracts}
                title={detail.title}
                selectedKey={selectedRoute}
                onSelect={setSelectedRoute}
              />
              <KeyMethodPanel methods={detail.methods} sources={detail.sources} />
            </Stack>
          )}
        </Box>

        {detail && (
          <Box
            sx={{
              flex: 1,
              minWidth: 420,
              borderLeft: '1px solid',
              borderColor: 'divider',
              p: 2.5,
            }}
            onMouseEnter={prefetchDiagram}
          >
            <EndpointDiagramPane
              repo={repo}
              fixture={fixture}
              entry={entry}
              onFullScreen={openDiagram}
              handlerFqn={selectedContract?.handler_fqn ?? ''}
            />
          </Box>
        )}
      </Box>

    </Box>
  )
}
