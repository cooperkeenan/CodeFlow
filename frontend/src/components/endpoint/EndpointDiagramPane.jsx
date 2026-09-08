import { useCallback, useMemo, useState } from 'react'
import { Box, Button, Typography } from '@mui/material'
import { endpointFixtureUrl } from '../../api/flow'
import { useFlowGraph } from '../../hooks/useFlowGraph'
import { useExpansion } from '../../hooks/useExpansion'
import { useGraphTransform } from '../../hooks/useGraphTransform'
import FlowCanvas from '../flow/FlowCanvas'
import { CANVAS, GRID } from '../flow/styles'
import { happyPath } from './happyPath'
import './happyPath.css'

const MONO = "'IBM Plex Mono', monospace"
const FIT_OPTIONS = { padding: 0.18, minZoom: 0.5, maxZoom: 1 }
const NOTE = { fontFamily: MONO, fontSize: 12, color: 'text.disabled', p: 2 }

export default function EndpointDiagramPane({ repo, fixture, entry, onFullScreen, handlerFqn = '' }) {
  const fixtureUrl = fixture && entry ? endpointFixtureUrl(entry) : null
  const { payload, loading, error } = useFlowGraph(repo, fixtureUrl, entry, null)
  const [isolated, setIsolated] = useState(null)

  const view = payload?.view ?? payload
  const links = payload?.links ?? null
  const expansion = useExpansion(view, false, [])
  const onIsolate = useCallback(id => setIsolated(prev => (prev === id ? null : id)), [])
  const { nodes: baseNodes, edges: baseEdges } = useGraphTransform(
    expansion, expansion.toggle, onIsolate, view?.node_geometry, links, null
  )
  const path = useMemo(
    () => happyPath(baseNodes, baseEdges, handlerFqn), [baseNodes, baseEdges, handlerFqn]
  )
  const nodes = useMemo(() => (
    path
      ? baseNodes.map(n => (
        path.nodeIds.has(n.id)
          ? { ...n, className: 'rf-happy' }
          : { ...n, data: { ...n.data, dimmed: n.type !== 'flowGroup' } }
      ))
      : baseNodes
  ), [baseNodes, path])
  const edges = useMemo(() => (
    path
      ? baseEdges.map(e => ({
        ...e,
        data: { ...e.data, happy: path.edgeIds.has(e.id), muted: !path.edgeIds.has(e.id) },
      }))
      : baseEdges
  ), [baseEdges, path])

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="overline" color="text.disabled">diagram</Typography>
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
            onPaneClick={() => setIsolated(null)}
            revealTrigger={expansion.lastReveal}
            repo={repo}
            fitOptions={FIT_OPTIONS}
          />
        )}
      </Box>
    </Box>
  )
}
