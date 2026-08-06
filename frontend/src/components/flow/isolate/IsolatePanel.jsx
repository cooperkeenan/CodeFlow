import { useEffect } from 'react'
import { useNodeExplanation } from '../../../hooks/useNodeExplanation'
import SourceRefList from '../SourceRefList'
import PrimarySummary from './PrimarySummary'
import MethodList from './MethodList'
import HelperList from './HelperList'
import { MONO, SURFACE_2, BORDER, TEXT, TEXT_MUTED } from '../styles'

const HEAD = { fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', color: TEXT_MUTED, margin: '12px 0 5px' }

function panelState(repo, nodeId, loading, error, explanation) {
  if (!repo || !nodeId) return 'unavailable'
  if (loading) return 'loading'
  if (error) return error.startsWith('404') ? 'unavailable' : 'error'
  if (explanation) return 'ready'
  return 'unavailable'
}

export default function IsolatePanel({ node, repo, repoUrl, onClose }) {
  const { explanation, loading, error } = useNodeExplanation(repo, node.id)
  const state = panelState(repo, node.id, loading, error, explanation)

  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const data = node.data

  return (
    <aside
      data-testid="isolate-panel"
      data-state={state}
      style={{
        position: 'absolute', top: 12, right: 12, zIndex: 7, width: 'min(520px, 42%)',
        maxHeight: 'calc(100% - 24px)', overflow: 'auto',
        background: SURFACE_2, border: `1px solid ${BORDER}`, borderRadius: 4, padding: '14px 16px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div>
          <div style={{ fontFamily: MONO, fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', color: TEXT_MUTED }}>
            {data.laneId}
          </div>
          <span style={{ fontFamily: MONO, fontSize: 13, fontWeight: 600, color: TEXT, lineHeight: 1.4 }}>{data.label}</span>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: TEXT_MUTED, cursor: 'pointer', fontSize: 18, lineHeight: 1, padding: 0 }}>×</button>
      </div>

      {data.oneLiner && (
        <p style={{ fontFamily: 'Instrument Sans, sans-serif', fontSize: 12, color: 'rgba(255,255,255,0.6)', lineHeight: 1.6, margin: '8px 0 0' }}>
          {data.oneLiner}
        </p>
      )}

      <div style={HEAD}>source</div>
      <SourceRefList refs={data.refs} repoUrl={repoUrl} />

      {state === 'loading' && (
        <div style={{ marginTop: 14 }}>
          {[0, 1, 2].map(i => (
            <div key={i} style={{ height: 10, marginBottom: 6, borderRadius: 2, background: 'rgba(255,255,255,0.06)', width: `${80 - i * 15}%` }} />
          ))}
        </div>
      )}

      {state === 'ready' && (
        <div style={{ marginTop: 2 }}>
          <PrimarySummary
            primaryKind={explanation.primary_kind}
            primaryName={explanation.primary_name}
            primarySummary={explanation.primary_summary}
            generated={explanation.generated}
          />
          <MethodList methods={explanation.methods} />
          <HelperList helpers={explanation.helpers} />
        </div>
      )}

      {(state === 'unavailable' || state === 'error') && (
        <div style={{ fontFamily: MONO, fontSize: 10, color: TEXT_MUTED, marginTop: 14 }}>
          {state === 'unavailable' ? 'no explanation available for this node' : error}
        </div>
      )}
    </aside>
  )
}
