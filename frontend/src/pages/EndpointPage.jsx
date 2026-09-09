import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Box, CircularProgress, Stack, Typography } from '@mui/material'
import { useEndpointDetail } from '../hooks/useEndpointDetail'
import { useRepoHome } from '../hooks/useRepoHome'
import EndpointRail from '../components/endpoint/EndpointRail'
import EndpointHeader from '../components/endpoint/EndpointHeader'
import { endpointDetailFixtureUrl } from '../api/endpoints'
import { flowQueryFn, flowQueryKey } from '../api/queries'
import ContractPanel from '../components/endpoint/ContractPanel'
import KeyMethodPanel from '../components/endpoint/KeyMethodPanel'
import EndpointDiagramPane from '../components/endpoint/EndpointDiagramPane'

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
  const [railOpen, setRailOpen] = useState(true)
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
      <EndpointHeader
        detail={detail}
        railOpen={railOpen}
        onToggleRail={() => setRailOpen(open => !open)}
        onBack={backToList}
      />

      <Box sx={{ flex: 1, minHeight: 0, display: 'flex' }}>
        <EndpointRail
          endpoints={home?.endpoints}
          open={railOpen}
          onOpen={selectEndpoint}
          onOverview={backToList}
          repo={repo}
          canPrefetch={!fixture}
          activeId={entry}
        />

        <Box
          sx={{
            flex: '1 1 45%',
            minWidth: 320,
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
            <Stack spacing={4} sx={{ p: 3 }}>
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
              flex: '1 1 55%',
              minWidth: 320,
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
