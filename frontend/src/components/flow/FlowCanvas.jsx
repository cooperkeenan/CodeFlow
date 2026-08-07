import { useState } from 'react'
import ReactFlow, { Background, Controls, MiniMap, ReactFlowProvider } from 'reactflow'
import 'reactflow/dist/style.css'
import './isolate.css'
import EntryNode from './nodes/EntryNode'
import StepNode from './nodes/StepNode'
import DecisionNode from './nodes/DecisionNode'
import PipelineNode from './nodes/PipelineNode'
import ParallelNode from './nodes/ParallelNode'
import EffectNode from './nodes/EffectNode'
import OutcomeNode from './nodes/OutcomeNode'
import LaneHeaderNode from './nodes/LaneHeaderNode'
import GroupBox from './nodes/GroupBox'
import FlowEdgeComponent from './FlowEdgeComponent'
import CameraController from './CameraController'
import { KIND_ACCENT } from './styles'
import { useIsolatedView } from '../../hooks/useIsolatedView'

const NODE_TYPES = {
  entry: EntryNode,
  step: StepNode,
  decision: DecisionNode,
  pipeline: PipelineNode,
  parallel: ParallelNode,
  effect: EffectNode,
  outcome: OutcomeNode,
  laneHeader: LaneHeaderNode,
  flowGroup: GroupBox,
}
const EDGE_TYPES = { flow: FlowEdgeComponent }
const FIT_OPTIONS = { padding: 0.25 }
const MINIMAP_THRESHOLD = 20

function FlowCanvasInner({ nodes, edges, selectedId, isolatedId, onPaneClick, revealTrigger, repo }) {
  const [hoveredEdge, setHoveredEdge] = useState(null)
  const { rfNodes, rfEdges, isolateCenter } = useIsolatedView(
    nodes, edges, selectedId, isolatedId, hoveredEdge, repo,
  )

  return (
    <ReactFlow
      nodes={rfNodes}
      edges={rfEdges}
      nodeTypes={NODE_TYPES}
      edgeTypes={EDGE_TYPES}
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
      <CameraController revealTrigger={revealTrigger} isolateCenter={isolateCenter} />
      <Background color="#242424" gap={28} size={1} style={{ background: '#1E1E1E' }} />
      <Controls position="top-left" style={{ background: '#1A1A1A', border: '1px solid #242424', borderRadius: 3 }} />
      {nodes.length > MINIMAP_THRESHOLD && (
        <MiniMap
          className={isolatedId ? 'rf-minimap-behind' : undefined}
          style={{ background: '#121212', border: '1px solid #242424' }}
          nodeColor={n => KIND_ACCENT[n.data?.kind] ?? '#333333'}
          maskColor="#00000088"
        />
      )}
    </ReactFlow>
  )
}

export default function FlowCanvas(props) {
  return (
    <ReactFlowProvider>
      <FlowCanvasInner {...props} />
    </ReactFlowProvider>
  )
}
