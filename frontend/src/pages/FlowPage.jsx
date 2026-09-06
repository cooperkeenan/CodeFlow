import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { endpointFixtureUrl, helperFixtureUrl } from '../api/flow'
import { useFlowGraph } from '../hooks/useFlowGraph'
import { useExpansion } from '../hooks/useExpansion'
import { useGraphTransform } from '../hooks/useGraphTransform'
import { useFlowEditing } from '../hooks/useFlowEditing'
import { appendCurrentView, parseTrail, viewUrl } from '../components/flow/viewTrail'
import FlowCanvas from '../components/flow/FlowCanvas'
import FlowHeader from '../components/flow/FlowHeader'
import Legend from '../components/flow/Legend'

const MONO = 'IBM Plex Mono, monospace'
const MUTED = { fontFamily: MONO, fontSize: 12, color: 'rgba(255,255,255,0.38)' }
const PANE_CLICK_GRACE_MS = 300
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
  const [isolated, setIsolated] = useState(null)
  const [showSecondary, setShowSecondary] = useState(false)

  const view = payload?.view ?? payload
  const links = payload?.links ?? null
  const pageTitle = payload?.page_title || analysis?.page_title || repo?.split('/').pop() || 'flow'
  const expansion = useExpansion(view, showSecondary, initialExpansion())
  const lastIsolateAt = useRef(0)
  const onIsolate = useCallback(nodeId => {
    lastIsolateAt.current = Date.now()
    setIsolated(prev => (prev === nodeId ? null : nodeId))
  }, [])
  const onLink = useCallback(link => {
    const kind = link.kind === 'helper' ? 'helper' : 'entry'
    const trail = appendCurrentView(parseTrail(fromParam), entry, helper)
    navigate(viewUrl(window.location.pathname, kind, link.target, trail))
  }, [navigate, fromParam, entry, helper])
  const { nodes: baseNodes, edges: baseEdges } = useGraphTransform(expansion, expansion.toggle, onIsolate, view?.node_geometry, links, onLink)
  const { editMode, toggleEditMode, nodes, edges, canvasProps, toolbar } = useFlowEditing(repo, baseNodes, baseEdges)
  const drawn = nodes.filter(n => n.type !== 'flowGroup').length
  const revealed = drawn - (view?.nodes?.length ?? 0)

  const onNodeClick = useCallback((_event, node) => {
    if (!node?.id?.startsWith(ENDPOINT_LINK_PREFIX)) return
    const target = node.id.slice(ENDPOINT_LINK_PREFIX.length)
    const trail = appendCurrentView(parseTrail(fromParam), entry, helper)
    navigate(viewUrl(window.location.pathname, 'entry', target, trail))
  }, [navigate, fromParam, entry, helper])

  const onPaneClick = useCallback(() => {
    if (Date.now() - lastIsolateAt.current < PANE_CLICK_GRACE_MS) return
    setIsolated(null)
  }, [])

  useEffect(() => {
    if (!isolated) return undefined
    const onKey = e => { if (e.key === 'Escape') setIsolated(null) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [isolated])

  return (
    <main style={{ height: '100vh', display: 'flex', flexDirection: 'column', padding: '1.1rem 1.4rem', gap: '0.9rem', boxSizing: 'border-box' }}>
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

      <div style={{ position: 'relative', flex: 1, minHeight: 0, border: '1px solid #232A36', borderRadius: 3, overflow: 'hidden', background: '#0F1218' }}>
        {error && <div style={{ ...MUTED, padding: '1rem' }}>failed to load flow: {error}</div>}
        {!error && loading && <div style={{ ...MUTED, padding: '1rem' }}>loading flow…</div>}
        {!error && !loading && !nodes.length && <div style={{ ...MUTED, padding: '1rem' }}>no flow data.</div>}
        {!error && !loading && nodes.length > 0 && (
          <>
            <FlowCanvas
              nodes={nodes}
              edges={edges}
              selectedId={isolated}
              isolatedId={isolated}
              onPaneClick={onPaneClick}
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
    </main>
  )
}
