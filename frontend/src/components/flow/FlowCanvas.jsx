import { useMemo, useState } from 'react'
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow'
import 'reactflow/dist/style.css'
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
import { KIND_ACCENT, CANVAS, GRID } from './styles'

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

export default function FlowCanvas({
  nodes, edges, selectedId, onNodeClick, onPaneClick, revealTrigger,
  focusIds = null, adjacentIds = null, packetIds = null, stepKey = 0, children = null,
}) {
  const [hoveredEdge, setHoveredEdge] = useState(null)

  const highlightNodes = useMemo(() => {
    const edge = edges.find(e => e.id === hoveredEdge)
    return edge ? new Set([edge.source, edge.target]) : new Set()
  }, [hoveredEdge, edges])

  const rfNodes = useMemo(() => nodes.map(n => ({
    ...n,
    selected: n.id === selectedId,
    data: {
      ...n.data,
      highlighted: highlightNodes.has(n.id),
      focused: !!focusIds?.has(n.id),
      adjacent: !focusIds?.has(n.id) && !!adjacentIds?.has(n.id),
      dimmed:
        !!focusIds?.size && !focusIds.has(n.id) && !adjacentIds?.has(n.id)
        && n.type !== 'flowGroup',
    },
  })), [nodes, selectedId, highlightNodes, focusIds, adjacentIds])

  const rfEdges = useMemo(() => edges.map(e => {
    const packet = !!packetIds?.size && [...packetIds].some(p => e.id.startsWith(`${p}:`))
    const inside = !!focusIds?.size && focusIds.has(e.source) && focusIds.has(e.target)
    const arriving = !!focusIds?.size && focusIds.has(e.target) && !focusIds.has(e.source)
    const flowing = packet || inside || arriving
    const near = !!adjacentIds?.size
      && (adjacentIds.has(e.source) || adjacentIds.has(e.target))
      && (focusIds?.has(e.source) || focusIds?.has(e.target)
          || adjacentIds.has(e.source) && adjacentIds.has(e.target))
    return {
      ...e,
      data: {
        ...e.data,
        highlighted: e.id === hoveredEdge,
        packet,
        flowing,
        stepKey,
        dimmed: !flowing && !near && !!focusIds?.size,
        near,
      },
    }
  }), [edges, hoveredEdge, packetIds, focusIds, adjacentIds, stepKey])

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
      <CameraController revealTrigger={revealTrigger} />
      {children}
      <Background color={GRID} gap={28} size={1} style={{ background: CANVAS }} />
      <Controls position="top-left" style={{ background: '#1A1A1A', border: '1px solid #242424', borderRadius: 3 }} />
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
