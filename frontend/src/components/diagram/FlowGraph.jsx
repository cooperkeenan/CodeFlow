import { useEffect } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow'
import 'reactflow/dist/style.css'
import CustomNode from './CustomNode'

const NODE_TYPES = { custom: CustomNode }

const FIT_VIEW_OPTIONS = { padding: 0.15 }

export default function FlowGraph({ nodes: externalNodes, edges: externalEdges, graphKey, onNodeClick }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(externalNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(externalEdges)

  useEffect(() => {
    setNodes(externalNodes)
    setEdges(externalEdges)
  }, [externalNodes, externalEdges, setNodes, setEdges])

  return (
    <ReactFlow
      key={graphKey}
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={onNodeClick}
      nodeTypes={NODE_TYPES}
      fitView
      fitViewOptions={FIT_VIEW_OPTIONS}
      minZoom={0.1}
      proOptions={{ hideAttribution: true }}
    >
      <Background color="#181818" gap={28} size={1} />
      <Controls
        style={{
          background: '#0f0f0f',
          border: '1px solid #1e1e1e',
          borderRadius: 3,
        }}
      />
      <MiniMap
        style={{ background: '#0a0a0a', border: '1px solid #1e1e1e' }}
        nodeColor={n => {
          const theme = {
            presentation: '#35a0f1',
            business: '#35f1a0',
            data: '#f1a035',
            external: '#c035f1',
          }
          return theme[n.data?.layer] ?? '#333'
        }}
        maskColor="#00000088"
      />
    </ReactFlow>
  )
}