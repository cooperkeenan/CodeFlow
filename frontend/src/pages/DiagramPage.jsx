import DiagramExplorer from '../components/diagram/DiagramExplorer'
import Badge from '../components/Badge'

export default function DiagramPage({ analysis, onBack }) {
  const { repo, profile, trace, diagram } = analysis
  const spec = trace?.diagram_spec
  const views = diagram?.views

  return (
    <main style={{
      height: '100vh', display: 'flex', flexDirection: 'column',
      padding: '1.25rem 1.5rem', gap: '1rem', boxSizing: 'border-box',
    }}>
      <header className="diagram-header">
        <button className="back" onClick={onBack}>← back</button>
        <div className="diagram-meta">
          <span className="diagram-repo">{repo?.split('/').pop()}</span>
          {profile?.architecture_type && <Badge>{profile.architecture_type}</Badge>}
          {profile?.language && <Badge>{profile.language}</Badge>}
          {profile?.framework && <Badge>{profile.framework}</Badge>}
        </div>
      </header>
      <div style={{ flex: 1, minHeight: 0 }}>
        {spec
          ? <DiagramExplorer spec={spec} views={views} />
          : <p style={{ color: '#3a3a3a', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12 }}>No diagram data.</p>
        }
      </div>
    </main>
  )
}
