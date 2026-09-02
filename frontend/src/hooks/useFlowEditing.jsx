import { useCallback, useMemo, useRef, useState } from 'react'
import { useDiagramEdits } from './useDiagramEdits'
import { applyEdits } from './graph/applyEdits'
import { useEditableCanvas } from '../components/diagram/edit/useEditableCanvas'
import EditToolbar from '../components/diagram/edit/EditToolbar'

const VIEW_ID = 'flow'
const NOOP = () => {}

export function useFlowEditing(repo, baseNodes, baseEdges) {
  const [editMode, setEditMode] = useState(false)
  const diagramEdits = useDiagramEdits(repo)
  const rfInstance = useRef(null)

  const overlay = diagramEdits.overlayFor(VIEW_ID)

  const { nodes, edges } = useMemo(() => {
    if (!editMode) return { nodes: baseNodes, edges: baseEdges }
    return applyEdits(baseNodes, baseEdges, overlay)
  }, [editMode, baseNodes, baseEdges, overlay])

  const onConnectEdge = useCallback(edge => {
    diagramEdits.addEdge(VIEW_ID, edge)
  }, [diagramEdits])

  const onDeleteElements = useCallback(({ nodeIds, edgeIds }) => {
    diagramEdits.deleteElements(VIEW_ID, { nodeIds, edgeIds })
  }, [diagramEdits])

  const onMoveNode = useCallback((nodeId, position) => {
    diagramEdits.moveNode(VIEW_ID, nodeId, position)
  }, [diagramEdits])

  const onSetEdgeMarker = useCallback((edgeId, markerEnd, markerStart) => {
    diagramEdits.setEdgeMarker(VIEW_ID, edgeId, markerEnd, markerStart)
  }, [diagramEdits])

  const onSetEdgeStyle = useCallback((edgeId, style) => {
    diagramEdits.setEdgeStyle(VIEW_ID, edgeId, style)
  }, [diagramEdits])

  const onAddText = useCallback(node => {
    diagramEdits.addTextNode(VIEW_ID, node)
  }, [diagramEdits])

  const onBumpTextFont = useCallback((nodeId, delta) => {
    diagramEdits.bumpTextFont(VIEW_ID, nodeId, delta)
  }, [diagramEdits])

  const onSetTextColor = useCallback((nodeId, color) => {
    diagramEdits.setTextColor(VIEW_ID, nodeId, color)
  }, [diagramEdits])

  const editable = useEditableCanvas({
    rfInstance,
    setNodes: NOOP,
    setEdges: NOOP,
    onConnectEdge,
    onDeleteElements,
    onMoveNode,
    onSetEdgeMarker,
    onSetEdgeStyle,
    onAddText,
    onBumpTextFont,
    onSetTextColor,
  })

  const onLabelCommit = useCallback((nodeId, label) => {
    diagramEdits.setNodeLabel(VIEW_ID, nodeId, label)
  }, [diagramEdits])

  const onTextCommit = useCallback((nodeId, text) => {
    diagramEdits.setTextNodeLabel(VIEW_ID, nodeId, text)
  }, [diagramEdits])

  const renderedNodes = useMemo(() => {
    if (!editMode) return nodes
    return editable.injectCallbacks(nodes, { onLabelCommit, onTextCommit })
  }, [editMode, nodes, editable, onLabelCommit, onTextCommit])

  const toggleEditMode = useCallback(() => setEditMode(v => !v), [])
  const onInit = useCallback(instance => { rfInstance.current = instance }, [])

  const canvasProps = editMode
    ? {
        editMode: true,
        onInit,
        onConnect: editable.onConnect,
        onNodesDelete: editable.onNodesDelete,
        onEdgesDelete: editable.onEdgesDelete,
        onNodeDragStop: editable.onNodeDragStop,
        onSelectionChange: editable.onSelectionChange,
      }
    : { editMode: false }

  const toolbar = editMode ? (
    <EditToolbar
      activeTool={editable.activeTool}
      hasSelection={editable.selectedNodeIds.length > 0 || editable.selectedEdgeIds.length > 0}
      hasEdgeSelection={editable.selectedEdgeIds.length > 0}
      hasTextSelection={editable.hasTextSelection}
      onSelectTool={editable.setActiveTool}
      onAddText={editable.handleAddText}
      onDelete={editable.handleDelete}
      onSetArrowhead={editable.handleSetArrowhead}
      onSetLineStyle={editable.handleSetLineStyle}
      onBumpFont={editable.handleBumpFont}
      onSetColor={editable.handleSetColor}
    />
  ) : null

  return { editMode, toggleEditMode, nodes: renderedNodes, edges, canvasProps, toolbar }
}
