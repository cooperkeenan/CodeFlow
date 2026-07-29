import { useMemo, useState } from 'react'
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow'
import 'reactflow/dist/style.css'
import EntryNode from './nodes/EntryNode'
import StepNode from './nodes/StepNode'
import DecisionNode from './nodes/DecisionNode'
import ParallelNode from './nodes/ParallelNode'
import EffectNode from './nodes/EffectNode'
import LaneHeaderNode from './nodes/LaneHeaderNode'
import FlowEdgeComponent from './FlowEdgeComponent'
import { KIND_ACCENT } from './styles'

const NODE_TYPES = {
  entry: EntryNode,
  step: StepNode,
  decision: DecisionNode,
  parallel: ParallelNode,
  effect: EffectNode,
  laneHeader: LaneHeaderNode,
}
const EDGE_TYPES = { flow: FlowEdgeComponent }
const FIT_OPTIONS = { padding: 0.25 }
const MINIMAP_THRESHOLD = 20

export default function FlowCanvas({ nodes, edges, selectedId, onNodeClick, onPaneClick }) {
  const [hoveredEdge, setHoveredEdge] = useState(null)

  const highlightNodes = useMemo(() => {
    const edge = edges.find(e => e.id === hoveredEdge)
    return edge ? new Set([edge.source, edge.target]) : new Set()
  }, [hoveredEdge, edges])

  const rfNodes = useMemo(() => nodes.map(n => ({
    ...n,
    selected: n.id === selectedId,
    data: { ...n.data, highlighted: highlightNodes.has(n.id) },
  })), [nodes, selectedId, highlightNodes])

  const rfEdges = useMemo(() => edges.map(e => ({
    ...e,
    data: { ...e.data, highlighted: e.id === hoveredEdge },
  })), [edges, hoveredEdge])

  return (
    <ReactFlow
      nodes={rfNodes}
      edges={rfEdges}
      nodeTypes={NODE_TYPES}
      edgeTypes={EDGE_TYPES}
      onNodeClick={onNodeClick}
      onPaneClick={onPaneClick}
      onEdgeMouseEnter={(_, edge) => setHoveredEdge(edge.id)}
      onEdgeMouseLeave={() => setHoveredEdge(null)}
      fitView
      fitViewOptions={FIT_OPTIONS}
      minZoom={0.1}
      nodesDraggable={false}
      nodesConnectable={false}
      proOptions={{ hideAttribution: true }}
    >
      <Background color="#242424" gap={28} size={1} style={{ background: '#1E1E1E' }} />
      <Controls style={{ background: '#1A1A1A', border: '1px solid #242424', borderRadius: 3 }} />
      {nodes.length > MINIMAP_THRESHOLD && (
        <MiniMap
          style={{ background: '#121212', border: '1px solid #242424' }}
          nodeColor={n => KIND_ACCENT[n.data?.kind] ?? '#333333'}
          maskColor="#00000088"
        />
      )}
    </ReactFlow>
  )
}
