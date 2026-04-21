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

const LAYER_COLORS = {
  presentation: { border: '#0d3b6e', bg: '#0d3b6e18', label: '#35a0f1' },
  business:     { border: '#0d4a28', bg: '#0d4a2818', label: '#35f1a0' },
  data:         { border: '#4a2e0d', bg: '#4a2e0d18', label: '#f1a035' },
  external:     { border: '#3a0d4a', bg: '#3a0d4a18', label: '#c035f1' },
}

function LayerGroupNode({ data }) {
  const theme = LAYER_COLORS[data.layer] ?? { border: '#2a2a2a', bg: '#2a2a2a18', label: '#888' }
  return (
    <div style={{
      width: '100%',
      height: '100%',
      border: `1px solid ${theme.border}`,
      borderRadius: 4,
      background: theme.bg,
      padding: '6px 10px',
      boxSizing: 'border-box',
    }}>
      <span style={{
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 9,
        letterSpacing: '0.14em',
        textTransform: 'uppercase',
        color: theme.label,
        fontWeight: 600,
      }}>
        {data.layer}
      </span>
    </div>
  )
}

const NODE_TYPES = { custom: CustomNode, layerGroup: LayerGroupNode }
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