import MermaidDiagram from '../components/MermaidDiagram'
import Badge from '../components/Badge'

export default function DiagramPage({ analysis, onBack }) {
  const { repo, profile, mermaid } = analysis

  return (
    <main className="diagram-page">
      <header className="diagram-header">
        <button className="back" onClick={onBack}>← back</button>
        <div className="diagram-meta">
          <span className="diagram-repo">{repo?.split('/').pop()}</span>
          <Badge>{profile?.architecture_type}</Badge>
          <Badge>{profile?.language}</Badge>
          <Badge>{profile?.framework}</Badge>
        </div>
      </header>

      <MermaidDiagram chart={mermaid} />

      <details className="raw">
        <summary>Mermaid source</summary>
        <pre>{mermaid}</pre>
      </details>

      <details className="raw">
        <summary>Diagram spec</summary>
        <pre>{JSON.stringify(analysis?.trace?.diagram_spec, null, 2)}</pre>
      </details>
    </main>
  )
}