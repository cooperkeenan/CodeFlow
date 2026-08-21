import { useEffect, useMemo, useState } from 'react'
import ReactFlow, { Background, Controls, MiniMap, ReactFlowProvider } from 'reactflow'
import 'reactflow/dist/style.css'
import './isolate.css'
import './reveal.css'
import { withRevealedNodes, withRevealedEdges, REVEAL_WINDOW_MS } from './revealTracking'
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
  card: CardNode,
  snippet: SnippetNode,
}
const EDGE_TYPES = { flow: FlowEdgeComponent }
const FIT_OPTIONS = { padding: 0.25 }
const MINIMAP_THRESHOLD = 20
const DEFAULT_CHROME = { controls: true, minimap: true }

function useActiveReveal(revealTrigger) {
  const [expired, setExpired] = useState(null)
  useEffect(() => {
    if (!revealTrigger || revealTrigger.fit) return undefined
    const timer = setTimeout(() => setExpired(revealTrigger), REVEAL_WINDOW_MS)
    return () => clearTimeout(timer)
  }, [revealTrigger])
  if (!revealTrigger || revealTrigger.fit || revealTrigger === expired) return null
  return revealTrigger
}

function FlowCanvasInner({
  nodes, edges, selectedId, isolatedId, onPaneClick, revealTrigger, repo,
  focusIds = null, adjacentIds = null, packetIds = null, stepKey = 0, children = null,
  visibleIds = null, enteringIds = null, suppressSelfLabels = false, chrome = DEFAULT_CHROME,
}) {
  const [hoveredEdge, setHoveredEdge] = useState(null)
  const { rfNodes, rfEdges, isolateCenter } = useIsolatedView(
    nodes, edges, selectedId, isolatedId, hoveredEdge, repo,
  )
  const activeReveal = useActiveReveal(revealTrigger)
  const revealedNodes = useMemo(() => withRevealedNodes(rfNodes, activeReveal), [rfNodes, activeReveal])
  const revealedEdges = useMemo(() => withRevealedEdges(rfEdges, activeReveal), [rfEdges, activeReveal])

  const focusOrder = useMemo(() => [...(focusIds ?? [])], [focusIds])
  const nodeLabelById = useMemo(() => {
    const map = new Map()
    for (const n of nodes) map.set(n.id, (n.data?.label ?? '').toString())
    return map
  }, [nodes])

  const stagedNodes = useMemo(() => {
    if (!focusIds && !visibleIds && !enteringIds) return revealedNodes
    return revealedNodes.map(n => {
      const entering = !!enteringIds?.has(n.id)
      return {
        ...n,
        hidden: !!visibleIds && !visibleIds.has(n.id),
        data: {
          ...n.data,
          focused: !!focusIds?.has(n.id),
          adjacent: !focusIds?.has(n.id) && !!adjacentIds?.has(n.id),
          dimmed:
            !!focusIds?.size && !focusIds.has(n.id) && !adjacentIds?.has(n.id)
            && n.type !== 'flowGroup',
          entering,
          enterDelay: entering ? focusOrder.indexOf(n.id) * 90 : 0,
        },
      }
    })
  }, [revealedNodes, focusIds, adjacentIds, visibleIds, enteringIds, focusOrder])

  const stagedEdges = useMemo(() => {
    if (!focusIds && !visibleIds && !enteringIds && !suppressSelfLabels) return revealedEdges
    return revealedEdges.map(e => {
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
          packet,
          flowing,
          stepKey,
          dimmed: !flowing && !near && !!focusIds?.size,
          near,
          entering: !!enteringIds?.has(e.target),
        },
      }
    })
  }, [revealedEdges, packetIds, focusIds, adjacentIds, stepKey, visibleIds, enteringIds,
      suppressSelfLabels, nodeLabelById])

  return (
    <ReactFlow
      nodes={stagedNodes}
      edges={stagedEdges}
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
      {children}
      <Background color={GRID} gap={28} size={1} style={{ background: CANVAS }} />
      {chrome.controls && (
        <Controls position="top-left" style={{ background: '#171C25', border: '1px solid #37415488', borderRadius: 3 }} />
      )}
      {chrome.minimap && nodes.length > MINIMAP_THRESHOLD && (
        <MiniMap
          className={isolatedId ? 'rf-minimap-behind' : undefined}
          style={{ background: '#12161E', border: '1px solid #37415488' }}
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
