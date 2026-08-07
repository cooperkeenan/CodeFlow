import { useEffect, useState } from 'react'
import { useNodeExplanation } from '../../../hooks/useNodeExplanation'
import PrimarySummary from './PrimarySummary'
import MethodList from './MethodList'
import HelperList from './HelperList'
import CodeView from './CodeView'
import SequenceView from './SequenceView'
import ViewToggle from './ViewToggle'
import { MONO, TEXT_MUTED } from '../styles'

const FILE_STYLE = {
  fontFamily: MONO,
  fontSize: 11,
  color: TEXT_MUTED,
  wordBreak: 'break-all',
  marginBottom: 10,
}

const ROOT_STYLE = {
  textAlign: 'left',
  width: '100%',
  height: '100%',
  display: 'flex',
  gap: 14,
}

const LEFT_COLUMN_STYLE = {
  flex: '0 0 30%',
  minWidth: 0,
  overflowY: 'auto',
  paddingRight: 14,
}

const PANE_STYLE = { flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', paddingRight: 6 }

const RIGHT_COLUMN_STYLE = {
  flex: '1 1 auto',
  minWidth: 0,
  minHeight: 0,
  display: 'flex',
  flexDirection: 'column',
}

function state(repo, nodeId, loading, error, explanation) {
  if (!repo || !nodeId) return 'unavailable'
  if (loading) return 'loading'
  if (error) return error.startsWith('404') ? 'unavailable' : 'error'
  return explanation ? 'ready' : 'unavailable'
}

function selectedName(explanation, fqn) {
  const all = [...(explanation?.methods ?? []), ...(explanation?.helpers ?? [])]
  return all.find(entry => entry.fqn === fqn)?.name ?? ''
}

export default function FrameContent({ repo, nodeId, provenance, collapsed, ready }) {
  const { explanation, sources, sequence, loading, error } = useNodeExplanation(repo, nodeId)
  const status = state(repo, nodeId, loading, error, explanation)
  const [selectedFqn, setSelectedFqn] = useState(null)
  const [mode, setMode] = useState('code')

  useEffect(() => {
    setSelectedFqn(null)
    setMode('code')
  }, [repo, nodeId])

  return (
    <div data-testid="frame-content" data-state={status} style={ROOT_STYLE}>
      <div style={LEFT_COLUMN_STYLE}>
        {provenance && <div style={FILE_STYLE}>{provenance}</div>}

        {status === 'loading' && [0, 1, 2].map(i => (
          <div
            key={i}
            style={{ height: 10, marginBottom: 6, borderRadius: 2, background: 'rgba(255,255,255,0.06)', width: `${80 - i * 15}%` }}
          />
        ))}

        {status === 'ready' && (
          <>
            <PrimarySummary
              primaryKind={explanation.primary_kind}
              primaryName={explanation.primary_name}
              primarySummary={explanation.primary_summary}
              generated={explanation.generated}
            />
            <MethodList methods={explanation.methods} onSelect={setSelectedFqn} selectedFqn={selectedFqn} />
            <HelperList helpers={explanation.helpers} onSelect={setSelectedFqn} selectedFqn={selectedFqn} />
          </>
        )}

        {(status === 'unavailable' || status === 'error') && (
          <div style={{ fontFamily: MONO, fontSize: 10, color: TEXT_MUTED }}>
            {status === 'unavailable' ? 'no explanation available for this node' : error}
          </div>
        )}
      </div>

      {!collapsed && (
        <div style={RIGHT_COLUMN_STYLE}>
          {ready && (
            <div className="rf-fade-in" style={PANE_STYLE}>
              <ViewToggle mode={mode} onChange={setMode} />
              {mode === 'code' ? (
                <CodeView fqn={selectedFqn} name={selectedName(explanation, selectedFqn)} source={sources?.[selectedFqn]} />
              ) : (
                <SequenceView sequence={sequence} />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
