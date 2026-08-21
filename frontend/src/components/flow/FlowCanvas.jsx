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
import CardNode from './nodes/CardNode'
import SnippetNode from './nodes/SnippetNode'
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
  card: CardNode,
  snippet: SnippetNode,
  flowGroup: GroupBox,
}
const EDGE_TYPES = { flow: FlowEdgeComponent }
const FIT_OPTIONS = { padding: 0.25 }
const MINIMAP_THRESHOLD = 20

const DEFAULT_CHROME = { controls: true, minimap: true }

export default function FlowCanvas({
  nodes, edges, selectedId, onNodeClick, onPaneClick, revealTrigger,
  focusIds = null, adjacentIds = null, packetIds = null, stepKey = 0, children = null,
  visibleIds = null, enteringIds = null, suppressSelfLabels = false,
  chrome = DEFAULT_CHROME,
}) {
  const [hoveredEdge, setHoveredEdge] = useState(null)

  const highlightNodes = useMemo(() => {
    const edge = edges.find(e => e.id === hoveredEdge)
    return edge ? new Set([edge.source, edge.target]) : new Set()
  }, [hoveredEdge, edges])

  const focusOrder = useMemo(() => [...(focusIds ?? [])], [focusIds])
  const nodeLabelById = useMemo(() => {
    const map = new Map()
    for (const n of nodes) map.set(n.id, (n.data?.label ?? '').toString())
    return map
  }, [nodes])

  const rfNodes = useMemo(() => nodes.map(n => {
    const entering = !!enteringIds?.has(n.id)
    return {
      ...n,
      selected: n.id === selectedId,
      hidden: !!visibleIds && !visibleIds.has(n.id),
      data: {
        ...n.data,
        highlighted: highlightNodes.has(n.id),
        focused: !!focusIds?.has(n.id),
        adjacent: !focusIds?.has(n.id) && !!adjacentIds?.has(n.id),
        dimmed:
          !!focusIds?.size && !focusIds.has(n.id) && !adjacentIds?.has(n.id)
          && n.type !== 'flowGroup',
        entering,
        enterDelay: entering ? focusOrder.indexOf(n.id) * 90 : 0,
      },
    }
  }), [nodes, selectedId, highlightNodes, focusIds, adjacentIds, visibleIds, enteringIds, focusOrder])

  const rfEdges = useMemo(() => edges.map(e => {
    const packet = !!packetIds?.size && [...packetIds].some(p => e.id.startsWith(`${p}:`))
    const inside = !!focusIds?.size && focusIds.has(e.source) && focusIds.has(e.target)
    const arriving = !!focusIds?.size && focusIds.has(e.target) && !focusIds.has(e.source)
    const flowing = packet || inside || arriving
    const near = !!adjacentIds?.size
      && (adjacentIds.has(e.source) || adjacentIds.has(e.target))
      && (focusIds?.has(e.source) || focusIds?.has(e.target)
          || adjacentIds.has(e.source) && adjacentIds.has(e.target))
    const hiddenEndpoint = id => !!visibleIds && !visibleIds.has(id)
    const selfLabel = suppressSelfLabels && e.label
      && e.label.toString().trim().toLowerCase() === (nodeLabelById.get(e.target) ?? '').trim().toLowerCase()
    return {
      ...e,
      hidden: hiddenEndpoint(e.source) && hiddenEndpoint(e.target),
      label: selfLabel ? undefined : e.label,
      data: {
        ...e.data,
        highlighted: e.id === hoveredEdge,
        packet,
        flowing,
        stepKey,
        dimmed: !flowing && !near && !!focusIds?.size,
        near,
        entering: !!enteringIds?.has(e.target),
      },
    }
  }), [edges, hoveredEdge, packetIds, focusIds, adjacentIds, stepKey, visibleIds, enteringIds, suppressSelfLabels, nodeLabelById])

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
      {chrome.controls && (
        <Controls position="top-left" style={{ background: '#171C25', border: '1px solid #37415488', borderRadius: 3 }} />
      )}
      {chrome.minimap && nodes.length > MINIMAP_THRESHOLD && (
        <MiniMap
          style={{ background: '#12161E', border: '1px solid #37415488' }}
          nodeColor={n => KIND_ACCENT[n.data?.kind] ?? '#333333'}
          maskColor="#00000088"
        />
      )}
    </ReactFlow>
  )
}
