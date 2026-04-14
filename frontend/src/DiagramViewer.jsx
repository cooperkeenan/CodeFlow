import React, { useEffect, useRef } from 'react'
import mermaid from 'mermaid'

mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' })

export default function DiagramViewer({ analysis, onBack }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current || !analysis?.mermaid) return
    const id = `mermaid-${Date.now()}`
    mermaid.render(id, analysis.mermaid).then(({ svg }) => {
      ref.current.innerHTML = svg
    }).catch(e => {
      ref.current.innerHTML = `<pre class="mermaid-error">${e.message}</pre>`
    })
  }, [analysis])

  const profile = analysis?.profile

  return (
    <div className="viewer">
      <div className="viewer-header">
        <button className="back-btn" onClick={onBack}>← back</button>
        <div className="viewer-meta">
          <span className="viewer-repo">{analysis?.repo?.split('/').pop()}</span>
          <span className="viewer-badge">{profile?.architecture_type}</span>
          <span className="viewer-badge">{profile?.language}</span>
          <span className="viewer-badge">{profile?.framework}</span>
        </div>
      </div>

      <div className="diagram-wrap" ref={ref} />

      <details className="raw-details">
        <summary>Raw Mermaid</summary>
        <pre className="raw-pre">{analysis?.mermaid}</pre>
      </details>

      <details className="raw-details">
        <summary>Diagram Spec</summary>
        <pre className="raw-pre">{JSON.stringify(analysis?.trace?.diagram_spec, null, 2)}</pre>
      </details>
    </div>
  )
}
