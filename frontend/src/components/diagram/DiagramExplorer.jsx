import { useState, useCallback } from 'react'
import FlowGraph from './FlowGraph'
import DetailPanel from './DetailPanel'
import Breadcrumb from './Breadcrumb'
import { useGraphTransform } from '../../hooks/useGraphTransform'

export default function DiagramExplorer({ spec }) {
  const [viewStack, setViewStack] = useState([])
  const [detailPanel, setDetailPanel] = useState(null)

  const focus = viewStack.at(-1) ?? null
  const { nodes, edges } = useGraphTransform(spec, focus)
  const graphKey = focus ? `${focus.kind}:${focus.id}` : 'system'

  const handleNodeClick = useCallback((_, node) => {
    const { label, drillable } = node.data
    if (node.type === 'moduleGroup') {
      if (focus?.kind === 'module' && focus.id === label) return
      setViewStack(prev => [...prev, { kind: 'module', id: label }])
      setDetailPanel(null)
    } else if (drillable) {
      setViewStack(prev => [...prev, { kind: 'component', id: label }])
      setDetailPanel(null)
    } else {
      setDetailPanel(prev => prev?.label === label ? null : node.data)
    }
  }, [focus])

  const navigateTo = useCallback(index => {
    setViewStack(prev => prev.slice(0, index))
    setDetailPanel(null)
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, height: '100%' }}>
      <Breadcrumb viewStack={viewStack} onNavigate={navigateTo} />

      <div style={{ display: 'flex', gap: 10, flex: 1, minHeight: 0 }}>
        <div style={{
          flex: 1,
          border: '1px solid #151515',
          borderRadius: 3,
          overflow: 'hidden',
          background: '#080808',
        }}>
          <FlowGraph
            nodes={nodes}
            edges={edges}
            graphKey={graphKey}
            onNodeClick={handleNodeClick}
          />
        </div>

        {detailPanel && (
          <DetailPanel
            data={detailPanel}
            onClose={() => setDetailPanel(null)}
          />
        )}
      </div>
    </div>
  )
}