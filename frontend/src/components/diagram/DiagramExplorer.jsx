import { useState, useCallback, useEffect, useMemo } from 'react'
import FlowGraph from './FlowGraph'
import DetailPanel from './DetailPanel'
import CodePanel from './CodePanel'
import Breadcrumb from './Breadcrumb'
import RationaleBox from './RationaleBox'
import { useGraphTransform } from '../../hooks/useGraphTransform'

export default function DiagramExplorer({ spec, views, diagramTemplates, codeViewMode, repo }) {
  const [viewStack, setViewStack] = useState([])
  const [detailPanel, setDetailPanel] = useState(null)
  const [codePanel, setCodePanel] = useState(null)
  const [expandedZones, setExpandedZones] = useState(() => new Set())
  const [expandedNodes, setExpandedNodes] = useState(() => new Set())

  const focus = viewStack.at(-1) ?? null
  const { nodes, edges } = useGraphTransform(spec, focus, expandedZones, expandedNodes, views)
  const graphKey = focus ? `${focus.kind}:${focus.id}` : 'system'

  const componentLocations = useMemo(() => {
    const map = {}
    if (!spec?.modules) return map
    for (const mod of spec.modules) {
      if (!mod.zones) continue
      for (const zone of Object.values(mod.zones)) {
        if (!Array.isArray(zone)) continue
        for (const comp of zone) {
          if (comp.name) {
            map[comp.name] = {
              file_path: comp.file_path ?? null,
              start_line: comp.start_line ?? null,
              end_line: comp.end_line ?? null,
            }
          }
        }
      }
    }
    return map
  }, [spec])

  useEffect(() => { setExpandedZones(new Set()); setExpandedNodes(new Set()) }, [graphKey])

  useEffect(() => { if (!codeViewMode) setCodePanel(null) }, [codeViewMode])

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
      setCodePanel(null)
    } else if (drillable && views && views[`component:${node.data.drillTarget || label}`]) {
      const drillId = node.data.drillTarget || label
      setViewStack(prev => {
        const i = prev.findIndex(e => e.kind === 'component' && e.id === drillId)
        return i >= 0 ? prev.slice(0, i + 1) : [...prev, { kind: 'component', id: drillId }]
      })
      setDetailPanel(null)
      setCodePanel(null)
    } else if (codeViewMode && componentLocations[label]?.file_path) {
      setCodePanel({ label, ...componentLocations[label] })
    } else if (node.data.description && !drillable) {
      setExpandedNodes(prev => {
        const next = new Set(prev)
        next.has(node.id) ? next.delete(node.id) : next.add(node.id)
        return next
      })
    } else {
      setDetailPanel(prev => prev?.label === label ? null : node.data)
    }
  }, [focus, views, codeViewMode, componentLocations])

  const navigateTo = useCallback(index => {
    setViewStack(prev => prev.slice(0, index))
    setDetailPanel(null)
    setCodePanel(null)
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, height: '100%' }}>
      <Breadcrumb viewStack={viewStack} onNavigate={navigateTo} />
      <RationaleBox
        rationale={diagramTemplates?.[graphKey]?.meta?.rationale}
        type={diagramTemplates?.[graphKey]?.type}
      />
      <div style={{ display: 'flex', gap: 10, flex: 1, minHeight: 0 }}>
        <div style={{ flex: 1, border: '1px solid #242424', borderRadius: 3, overflow: 'hidden', background: '#1E1E1E' }}>
          <FlowGraph nodes={nodes} edges={edges} graphKey={graphKey} onNodeClick={handleNodeClick} />
        </div>
        {codePanel
          ? <CodePanel
              repo={repo}
              label={codePanel.label}
              file_path={codePanel.file_path}
              start_line={codePanel.start_line}
              end_line={codePanel.end_line}
              onClose={() => setCodePanel(null)}
            />
          : detailPanel && <DetailPanel data={detailPanel} onClose={() => setDetailPanel(null)} />
        }
      </div>
    </div>
  )
}
