import { useQueryClient } from '@tanstack/react-query'
import { repoHomeQueryKey } from '../../api/queries'
import { parseTrail, viewUrl } from './viewTrail'
import Breadcrumb from './Breadcrumb'

const MONO = 'IBM Plex Mono, monospace'
const MUTED = { fontFamily: MONO, fontSize: 12, color: 'rgba(255,255,255,0.38)' }
const REPO_HOME_FIXTURE = '/fixture/repo_home.json'

export default function FlowHeader({
  pageTitle, entry, helper, repo, fixture, fromParam, pathname, navigate, onBack,
  showSecondary, onToggleSecondary, revealed, onCollapseAll, editMode, onToggleEditMode,
  drawn, viewNodeCount, loading, error,
}) {
  const queryClient = useQueryClient()
  const trail = parseTrail(fromParam)
  const inEndpointView = Boolean(entry || helper)
  const home = queryClient.getQueryData(repoHomeQueryKey(repo, fixture ? REPO_HOME_FIXTURE : null))

  const onNavigate = index => {
    const step = trail[index]
    navigate(viewUrl(pathname, step.kind, step.value, trail.slice(0, index)))
  }

  return (
    <header style={{ display: 'flex', alignItems: 'center', gap: '1.2rem', flexWrap: 'wrap' }}>
      {inEndpointView ? (
        <Breadcrumb trail={trail} currentTitle={pageTitle} home={home} onBack={onBack} onNavigate={onNavigate} />
      ) : (
        <>
          <button className="back" onClick={onBack}>← repos</button>
          <h1 style={{ fontFamily: MONO, fontSize: '1.25rem', fontWeight: 600, color: 'rgba(255,255,255,0.87)', margin: 0 }}>
            {pageTitle}
          </h1>
        </>
      )}
      {helper && (
        <span style={{ fontFamily: MONO, fontSize: 11, color: 'rgba(255,255,255,0.5)' }}>shared helper</span>
      )}
      {repo && <span style={{ fontFamily: MONO, fontSize: 11, color: 'rgba(255,255,255,0.38)' }}>{repo}</span>}
      <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
        {!loading && !error && (
          <>
            <button className="back" onClick={onToggleSecondary}>
              {showSecondary ? 'hide cross-links' : 'show cross-links'}
            </button>
            {revealed > 0 && (
              <button className="back" onClick={onCollapseAll}>collapse all</button>
            )}
            <button className="back" onClick={onToggleEditMode}>{editMode ? 'done' : 'edit'}</button>
            <span style={MUTED}>
              {revealed > 0 ? `${viewNodeCount} + ${revealed} revealed` : `${drawn} nodes`}
            </span>
          </>
        )}
        {(loading || error) && <span style={MUTED}>{loading ? 'loading…' : 'error'}</span>}
      </span>
    </header>
  )
}
