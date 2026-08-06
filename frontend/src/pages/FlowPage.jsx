import { useCallback, useState } from 'react'
import { useFlowGraph } from '../hooks/useFlowGraph'
import { useExpansion } from '../hooks/useExpansion'
import { useGraphTransform } from '../hooks/useGraphTransform'
import FlowCanvas from '../components/flow/FlowCanvas'
import Legend from '../components/flow/Legend'
import IsolatePanel from '../components/flow/isolate/IsolatePanel'

const MONO = 'IBM Plex Mono, monospace'
const MUTED = { fontFamily: MONO, fontSize: 12, color: 'rgba(255,255,255,0.38)' }

function initialExpansion() {
  if (typeof window === 'undefined') return []
  const raw = new URLSearchParams(window.location.search).get('expand')
  return raw ? raw.split(',').filter(Boolean) : []
}

export default function FlowPage({ analysis, onBack, fixture }) {
  const repo = analysis?.repo
  const { payload, loading, error } = useFlowGraph(repo, fixture)
  const [isolated, setIsolated] = useState(null)
  const [showSecondary, setShowSecondary] = useState(false)

  const view = payload?.view ?? payload
  const repoUrl = payload?.repo_url ?? null
  const pageTitle = payload?.page_title || analysis?.page_title || repo?.split('/').pop() || 'flow'
  const expansion = useExpansion(view, showSecondary, initialExpansion())
  const onIsolate = useCallback(nodeId => {
    setIsolated(prev => (prev === nodeId ? null : nodeId))
  }, [])
  const { nodes, edges } = useGraphTransform(expansion, expansion.toggle, onIsolate, view?.node_geometry)
  const drawn = nodes.filter(n => n.type !== 'flowGroup').length
  const revealed = drawn - (view?.nodes?.length ?? 0)
  const selectedNode = isolated ? nodes.find(n => n.id === isolated) ?? null : null

  const onPaneClick = useCallback(() => setIsolated(null), [])

  return (
    <main style={{ height: '100vh', display: 'flex', flexDirection: 'column', padding: '1.1rem 1.4rem', gap: '0.9rem', boxSizing: 'border-box' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: '1.2rem', flexWrap: 'wrap' }}>
        <button className="back" onClick={onBack}>← repos</button>
        <h1 style={{ fontFamily: MONO, fontSize: '1.25rem', fontWeight: 600, color: 'rgba(255,255,255,0.87)', margin: 0 }}>
          {pageTitle}
        </h1>
        {repo && <span style={{ fontFamily: MONO, fontSize: 11, color: 'rgba(255,255,255,0.38)' }}>{repo}</span>}
        <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
          {!loading && !error && (
            <>
              <button className="back" onClick={() => setShowSecondary(v => !v)}>
                {showSecondary ? 'hide cross-links' : 'show cross-links'}
              </button>
              {revealed > 0 && (
                <button className="back" onClick={expansion.collapseAll}>collapse all</button>
              )}
              <span style={MUTED}>
                {revealed > 0 ? `${view?.nodes?.length ?? 0} + ${revealed} revealed` : `${drawn} nodes`}
              </span>
            </>
          )}
          {(loading || error) && <span style={MUTED}>{loading ? 'loading…' : 'error'}</span>}
        </span>
      </header>

      <div style={{ position: 'relative', flex: 1, minHeight: 0, border: '1px solid #242424', borderRadius: 3, overflow: 'hidden', background: '#1E1E1E' }}>
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
              revealTrigger={expansion.lastReveal}
            />
            <Legend />
            {selectedNode && (
              <IsolatePanel node={selectedNode} repo={repo} repoUrl={repoUrl} onClose={() => setIsolated(null)} />
            )}
          </>
        )}
      </div>
    </main>
  )
}
