import { useEffect, useRef, useCallback } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow'
import 'reactflow/dist/style.css'
import CustomNode from './CustomNode'
import ModuleGroupNode from './nodes/ModuleGroupNode'
import ZoneGroupNode from './nodes/ZoneGroupNode'
import ClusterGroupNode from './nodes/ClusterGroupNode'
import ModuleSummaryNode from './nodes/ModuleSummaryNode'
import ModuleGhostNode from './nodes/ModuleGhostNode'
import ZoneMoreNode from './nodes/ZoneMoreNode'

const NODE_W = 180
const NODE_H = 58

const NODE_TYPES = {
  custom: CustomNode,
  moduleGroup: ModuleGroupNode,
  zoneGroup: ZoneGroupNode,
  clusterGroup: ClusterGroupNode,
  moduleSummary: ModuleSummaryNode,
  moduleGhost: ModuleGhostNode,
  zoneMore: ZoneMoreNode,
}
const FIT_VIEW_OPTIONS = { padding: 0.3, maxZoom: 1 }


export default function FlowGraph({ nodes: externalNodes, edges: externalEdges, onNodeClick }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(externalNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(externalEdges)
  const rfInstance = useRef(null)

  useEffect(() => {
    setNodes(externalNodes)
    setEdges(externalEdges)
    setTimeout(() => {
      rfInstance.current?.fitView({ padding: 0.3, maxZoom: 1, duration: 300 })
    }, 50)
  }, [externalNodes, externalEdges, setNodes, setEdges])

  const handleNodeClick = useCallback((event, node) => {
    if (node.type === 'zoneGroup' || node.type === 'clusterGroup' || node.type === 'moduleGhost') return
    const noCenter = node.type === 'moduleGroup' || node.type === 'moduleSummary' || node.type === 'zoneMore'
    if (rfInstance.current && !noCenter && !node.data.drillable) {
      const { zoom } = rfInstance.current.getViewport()
      const absX = (node.positionAbsolute?.x ?? node.position.x) + NODE_W / 2
      const absY = (node.positionAbsolute?.y ?? node.position.y) + NODE_H / 2
      rfInstance.current.setCenter(absX, absY, { duration: 350, zoom })
    }
    onNodeClick(event, node)
  }, [onNodeClick])

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={handleNodeClick}
      onInit={instance => { rfInstance.current = instance }}
      nodeTypes={NODE_TYPES}
      fitView
      fitViewOptions={FIT_VIEW_OPTIONS}
      minZoom={0.1}
      proOptions={{ hideAttribution: true }}
    >
      <Background color="#242424" gap={28} size={1} style={{ background: '#1E1E1E' }} />
      <Controls style={{ background: '#1A1A1A', border: '1px solid #242424', borderRadius: 3 }} />
      <MiniMap
        style={{ background: '#121212', border: '1px solid #242424' }}
        nodeColor={n => n.data?.color?.accent ?? '#333333'}
        maskColor="#00000088"
      />
    </ReactFlow>
  )
}
