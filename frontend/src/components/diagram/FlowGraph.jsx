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

const NODE_W = 180
const NODE_H = 58

function ModuleGroupNode({ data }) {
  const { color } = data
  return (
    <div style={{
      width: '100%', height: '100%',
      border: `1px solid ${color.border}`,
      borderRadius: 6,
      background: `${color.bg}55`,
      pointerEvents: 'none',
      boxSizing: 'border-box',
    }}>
      <span
        className="nodrag"
        title="Click to focus this module"
        style={{
          position: 'absolute', top: 6, left: 10,
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 11, letterSpacing: '0.08em',
          color: color.accent, fontWeight: 700,
          pointerEvents: 'auto', cursor: 'pointer',
          padding: '2px 4px', borderRadius: 3,
        }}
      >
        {data.label} <span style={{ opacity: 0.5, fontSize: 9 }}>⤢</span>
      </span>
    </div>
  )
}

function ZoneGroupNode({ data }) {
  const { color } = data
  return (
    <div style={{
      width: '100%', height: '100%',
      border: `1px dashed ${color.border}`,
      borderRadius: 4,
      background: 'transparent',
      pointerEvents: 'none',
      boxSizing: 'border-box',
    }}>
      <span style={{
        position: 'absolute', top: 5, left: 9,
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 8, letterSpacing: '0.14em',
        textTransform: 'uppercase',
        color: '#777', fontWeight: 600,
      }}>
        {data.label}
      </span>
    </div>
  )
}

const NODE_TYPES = { custom: CustomNode, moduleGroup: ModuleGroupNode, zoneGroup: ZoneGroupNode }
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
    if (node.type === 'zoneGroup') return
    if (rfInstance.current && node.type !== 'moduleGroup' && !node.data.drillable) {
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
      <Background color="#181818" gap={28} size={1} />
      <Controls style={{ background: '#0f0f0f', border: '1px solid #1e1e1e', borderRadius: 3 }} />
      <MiniMap
        style={{ background: '#0a0a0a', border: '1px solid #1e1e1e' }}
        nodeColor={n => n.data?.color?.accent ?? '#333'}
        maskColor="#00000088"
      />
    </ReactFlow>
  )
}
