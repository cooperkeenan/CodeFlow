import { useEffect, useRef } from 'react'
import mermaid from 'mermaid'

mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' })

export default function MermaidDiagram({ chart }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current || !chart) return
    mermaid
      .render(`mermaid-${Date.now()}`, chart)
      .then(({ svg }) => { ref.current.innerHTML = svg })
      .catch(e => { ref.current.innerHTML = `<pre class="error">${e.message}</pre>` })
  }, [chart])

  return <div ref={ref} className="mermaid-wrap" />
}