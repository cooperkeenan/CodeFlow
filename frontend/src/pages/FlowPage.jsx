import { CANVAS, GRID } from '../components/flow/styles'
import { useCallback, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { endpointFixtureUrl, helperFixtureUrl } from '../api/flow'
import { useFlowGraph } from '../hooks/useFlowGraph'
import { useExpansion } from '../hooks/useExpansion'
import { useGraphTransform } from '../hooks/useGraphTransform'
import { useFlowEditing } from '../hooks/useFlowEditing'
import { appendCurrentView, parseTrail, viewUrl } from '../components/flow/viewTrail'
import FlowCanvas from '../components/flow/FlowCanvas'
import FlowHeader from '../components/flow/FlowHeader'
import EndpointSidebar from '../components/flow/EndpointSidebar'
import Legend from '../components/flow/Legend'
import { brainstormUrl } from '../components/flow/brainstormLink'

const MONO = 'IBM Plex Mono, monospace'
const MUTED = { fontFamily: MONO, fontSize: 12, color: 'rgba(255,255,255,0.38)' }
const ENDPOINT_LINK_PREFIX = 'endlink:'

function initialExpansion() {
  if (typeof window === 'undefined') return []
  const raw = new URLSearchParams(window.location.search).get('expand')
  return raw ? raw.split(',').filter(Boolean) : []
}

export default function FlowPage({ analysis, onBack, fixture }) {
  const repo = analysis?.repo
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const entry = params.get('entry')
  const helper = params.get('helper')
  const fromParam = params.get('from')
  const fixtureUrl = fixture
    ? (helper ? helperFixtureUrl(helper) : entry ? endpointFixtureUrl(entry) : fixture)
    : fixture
  const { payload, loading, error } = useFlowGraph(repo, fixtureUrl, entry, helper)
  const [showSecondary, setShowSecondary] = useState(false)

  const view = payload?.view ?? payload
  const links = payload?.links ?? null
  const pageTitle = payload?.page_title || analysis?.page_title || repo?.split('/').pop() || 'flow'
  const expansion = useExpansion(view, showSecondary, initialExpansion())
  const onLink = useCallback(link => {
    const kind = link.kind === 'helper' ? 'helper' : 'entry'
    const trail = appendCurrentView(parseTrail(fromParam), entry, helper)
    navigate(viewUrl(window.location.pathname, kind, link.target, trail))
  }, [navigate, fromParam, entry, helper])
  const { nodes: baseNodes, edges: baseEdges } = useGraphTransform(expansion, expansion.toggle, view?.node_geometry, links, onLink)
  const { editMode, toggleEditMode, nodes, edges, canvasProps, toolbar } = useFlowEditing(repo, baseNodes, baseEdges)
  const drawn = nodes.filter(n => n.type !== 'flowGroup').length
  const revealed = drawn - (view?.nodes?.length ?? 0)

  const onNodeClick = useCallback((_event, node) => {
    if (!node?.id?.startsWith(ENDPOINT_LINK_PREFIX)) return
    const target = node.id.slice(ENDPOINT_LINK_PREFIX.length)
    const trail = appendCurrentView(parseTrail(fromParam), entry, helper)
    navigate(viewUrl(window.location.pathname, 'entry', target, trail))
  }, [navigate, fromParam, entry, helper])

  const onNodeDoubleClick = useCallback((_event, node) => {
    if (editMode) return
    const url = brainstormUrl(repo, node)
    if (url) navigate(url)
  }, [editMode, repo, navigate])

  return (
    <main className="area-rail" style={{ height: '100vh', display: 'flex', boxSizing: 'border-box' }}>
      <EndpointSidebar
        repo={repo}
        fixture={fixture}
        entry={entry}
        flowPath={window.location.pathname}
        endpointPath={fixture ? '/endpoint-fixture' : '/endpoint'}
      />
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', padding: '1.1rem 1.4rem', gap: '0.9rem', boxSizing: 'border-box' }}>
        <FlowHeader
          pageTitle={pageTitle}
          entry={entry}
          helper={helper}
          repo={repo}
          fixture={fixture}
          fromParam={fromParam}
          pathname={window.location.pathname}
          navigate={navigate}
          onBack={onBack}
          showSecondary={showSecondary}
          onToggleSecondary={() => setShowSecondary(v => !v)}
          revealed={revealed}
          onCollapseAll={expansion.collapseAll}
          editMode={editMode}
          onToggleEditMode={toggleEditMode}
          drawn={drawn}
          viewNodeCount={view?.nodes?.length ?? 0}
          loading={loading}
          error={error}
        />

        <div style={{ position: 'relative', flex: 1, minHeight: 0, border: `1px solid ${GRID}`, borderRadius: 3, overflow: 'hidden', background: CANVAS }}>
          {error && <div style={{ ...MUTED, padding: '1rem' }}>failed to load flow: {error}</div>}
          {!error && loading && <div style={{ ...MUTED, padding: '1rem' }}>loading flow…</div>}
          {!error && !loading && !nodes.length && <div style={{ ...MUTED, padding: '1rem' }}>no flow data.</div>}
          {!error && !loading && nodes.length > 0 && (
            <>
              <FlowCanvas
                nodes={nodes}
                edges={edges}
                onNodeDoubleClick={onNodeDoubleClick}
                onNodeClick={onNodeClick}
                revealTrigger={expansion.lastReveal}
                repo={repo}
                {...canvasProps}
              >
                {toolbar}
              </FlowCanvas>
              <Legend />
            </>
          )}
        </div>
      </div>
    </main>
  )
}
