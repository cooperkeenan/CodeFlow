import { useCallback, useMemo, useState } from 'react'
import { Box, Button, Typography } from '@mui/material'
import { endpointFixtureUrl } from '../../api/flow'
import { useFlowGraph } from '../../hooks/useFlowGraph'
import { useExpansion } from '../../hooks/useExpansion'
import { useGraphTransform } from '../../hooks/useGraphTransform'
import { useHappyHighlight } from '../../hooks/useHappyHighlight'
import FlowCanvas from '../flow/FlowCanvas'
import { CANVAS, GRID } from '../flow/styles'
import './happyPath.css'

const MONO = "'IBM Plex Mono', monospace"
const FIT_OPTIONS = { padding: 0.18, minZoom: 0.5, maxZoom: 1 }
const NOTE = { fontFamily: MONO, fontSize: 12, color: 'text.disabled', p: 2 }

const ENDPOINT_LINK_PREFIX = 'endlink:'
const NO_IDS = []

export default function EndpointDiagramPane({ repo, fixture, entry, onFullScreen, contract = null, onLink = null }) {
  const fixtureUrl = fixture && entry ? endpointFixtureUrl(entry) : null
  const { payload, loading, error } = useFlowGraph(repo, fixtureUrl, entry, null)
  const [isolated, setIsolated] = useState(null)
  const [partial, setPartial] = useState(null)

  const view = payload?.view ?? payload
  const links = payload?.links ?? null
  const happy = useMemo(() => (
    contract
      ? (payload?.paths ?? []).find(path => (
        path.method === contract.method
        && path.path === contract.path
        && path.handler_fqn === contract.handler_fqn
      )) ?? null
      : null
  ), [payload, contract])
  const forcedIds = happy?.reveal?.length ? happy.reveal : NO_IDS
  const expansion = useExpansion(view, false, [], forcedIds)
  const onIsolate = useCallback(id => setIsolated(prev => (prev === id ? null : id)), [])
  const { nodes: baseNodes, edges: baseEdges } = useGraphTransform(
    expansion, expansion.toggle, onIsolate, view?.node_geometry, links, onLink
  )
  const onNodeClick = useCallback((_event, node) => {
    if (node?.id?.startsWith(ENDPOINT_LINK_PREFIX)) {
      onLink?.({ kind: 'endpoint', target: node.id.slice(ENDPOINT_LINK_PREFIX.length) })
    }
  }, [onLink])
  const { nodes, edges, fitNodeIds } = useHappyHighlight(baseNodes, baseEdges, happy)

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="overline" color="text.disabled">diagram</Typography>
        {happy?.ends_in_failure && (
          <Typography sx={{ fontFamily: MONO, fontSize: 12, color: '#F5A524' }}>
            no success route found statically
          </Typography>
        )}
        {partial && (
          <Typography data-testid="path-partial" sx={{ fontFamily: MONO, fontSize: 12, color: 'text.secondary' }}>
            path continues — showing {partial.shown} of {partial.total} steps
          </Typography>
        )}
        <Box sx={{ flexGrow: 1 }} />
        <Button
          size="small"
          variant="outlined"
          data-testid="view-diagram"
          onClick={onFullScreen}
          sx={{ fontFamily: MONO, fontSize: 12 }}
        >
          full screen
        </Button>
      </Box>
      <Box
        data-testid="endpoint-diagram"
        data-happy-ids={happy ? JSON.stringify(happy.node_ids) : undefined}
        data-happy-edges={happy ? JSON.stringify(happy.edges) : undefined}
        sx={{
          position: 'relative',
          flex: 1,
          minHeight: 0,
          border: `1px solid ${GRID}`,
          borderRadius: '3px',
          overflow: 'hidden',
          background: CANVAS,
        }}
      >
        {error && <Typography sx={NOTE}>failed to load diagram: {error}</Typography>}
        {!error && loading && <Typography sx={NOTE}>loading diagram…</Typography>}
        {!error && !loading && !nodes.length && <Typography sx={NOTE}>no diagram data.</Typography>}
        {!error && !loading && nodes.length > 0 && (
          <FlowCanvas
            nodes={nodes}
            edges={edges}
            selectedId={isolated}
            isolatedId={isolated}
            onNodeClick={onNodeClick}
            onPaneClick={() => setIsolated(null)}
            revealTrigger={expansion.lastReveal}
            repo={repo}
            fitOptions={FIT_OPTIONS}
            fitNodeIds={fitNodeIds}
            onFitPartial={setPartial}
          />
        )}
      </Box>
    </Box>
  )
}
