import { useState, useCallback, useEffect } from 'react'
import FlowGraph from './FlowGraph'
import DetailPanel from './DetailPanel'
import Breadcrumb from './Breadcrumb'
import { useGraphTransform } from '../../hooks/useGraphTransform'

export default function DiagramExplorer({ spec, views }) {
  const [viewStack, setViewStack] = useState([])
  const [detailPanel, setDetailPanel] = useState(null)
  const [expandedZones, setExpandedZones] = useState(() => new Set())

  const focus = viewStack.at(-1) ?? null
  const { nodes, edges } = useGraphTransform(spec, focus, expandedZones, views)
  const graphKey = focus ? `${focus.kind}:${focus.id}` : 'system'

  useEffect(() => { setExpandedZones(new Set()) }, [graphKey])

  const handleNodeClick = useCallback((_, node) => {
    const { label, drillable } = node.data
    if (node.type === 'moduleGhost' || node.type === 'zoneGroup' || node.type === 'clusterGroup') return
    if (node.type === 'zoneMore') {
      setExpandedZones(prev => {
        const next = new Set(prev)
        next.has(node.data.key) ? next.delete(node.data.key) : next.add(node.data.key)
        return next
      })
    } else if (node.type === 'moduleGroup' || node.type === 'moduleSummary') {
      setViewStack(prev => {
        const i = prev.findIndex(e => e.kind === 'module' && e.id === label)
        return i >= 0 ? prev.slice(0, i + 1) : [...prev, { kind: 'module', id: label }]
      })
      setDetailPanel(null)
    } else if (drillable && views && views[`component:${label}`]) {
      setViewStack(prev => {
        const i = prev.findIndex(e => e.kind === 'component' && e.id === label)
        return i >= 0 ? prev.slice(0, i + 1) : [...prev, { kind: 'component', id: label }]
      })
      setDetailPanel(null)
    } else {
      setDetailPanel(prev => prev?.label === label ? null : node.data)
    }
  }, [focus, views])

  const navigateTo = useCallback(index => {
    setViewStack(prev => prev.slice(0, index))
    setDetailPanel(null)
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, height: '100%' }}>
      <Breadcrumb viewStack={viewStack} onNavigate={navigateTo} />
      <div style={{ display: 'flex', gap: 10, flex: 1, minHeight: 0 }}>
        <div style={{ flex: 1, border: '1px solid #242424', borderRadius: 3, overflow: 'hidden', background: '#1E1E1E' }}>
          <FlowGraph nodes={nodes} edges={edges} graphKey={graphKey} onNodeClick={handleNodeClick} />
        </div>
        {detailPanel && <DetailPanel data={detailPanel} onClose={() => setDetailPanel(null)} />}
      </div>
    </div>
  )
}
