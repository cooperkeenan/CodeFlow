import { useState, useRef, useCallback } from 'react'
import { buildNewEdge, markerForArrowhead, styleForLineStyle } from './edgeMarkers'

const FONT_MIN = 8
const FONT_MAX = 48
const FONT_DEFAULT = 13

export function useEditableCanvas({
  rfInstance,
  setNodes,
  setEdges,
  onConnectEdge,
  onDeleteElements,
  onMoveNode,
  onSetEdgeMarker,
  onSetEdgeStyle,
  onAddText,
  onBumpTextFont,
  onSetTextColor,
}) {
  const [selectedNodeIds, setSelectedNodeIds] = useState([])
  const [selectedEdgeIds, setSelectedEdgeIds] = useState([])
  const [selectedTextNodeIds, setSelectedTextNodeIds] = useState([])
  const [activeTool, setActiveTool] = useState('select')
  const selectionRef = useRef({ nodeIds: [], edgeIds: [] })

  const onConnect = useCallback((params) => {
    const edge = buildNewEdge(params)
    onConnectEdge(edge)
  }, [onConnectEdge])

  const onNodesDelete = useCallback((deleted) => {
    onDeleteElements({ nodeIds: deleted.map(n => n.id), edgeIds: [] })
  }, [onDeleteElements])

  const onEdgesDelete = useCallback((deleted) => {
    onDeleteElements({ nodeIds: [], edgeIds: deleted.map(e => e.id) })
  }, [onDeleteElements])

  const onNodeDragStop = useCallback((_, node) => {
    onMoveNode(node.id, node.position)
  }, [onMoveNode])

  const onSelectionChange = useCallback(({ nodes, edges }) => {
    const nodeIds = nodes.map(n => n.id)
    const edgeIds = edges.map(e => e.id)
    const textIds = nodes.filter(n => n.type === 'text').map(n => n.id)
    selectionRef.current = { nodeIds, edgeIds }
    setSelectedNodeIds(nodeIds)
    setSelectedEdgeIds(edgeIds)
    setSelectedTextNodeIds(textIds)
  }, [])

  const handleAddText = useCallback(() => {
    const rf = rfInstance.current
    if (!rf) return
    const centerX = window.innerWidth / 2
    const centerY = window.innerHeight / 2
    const pos = rf.screenToFlowPosition({ x: centerX, y: centerY })
    const node = {
      id: `text-${Date.now()}`,
      type: 'text',
      position: pos,
      data: { text: 'Text' },
    }
    onAddText(node)
  }, [rfInstance, onAddText])

  const handleDelete = useCallback(() => {
    if (selectedNodeIds.length === 0 && selectedEdgeIds.length === 0) return
    onDeleteElements({ nodeIds: selectedNodeIds, edgeIds: selectedEdgeIds })
  }, [selectedNodeIds, selectedEdgeIds, onDeleteElements])

  const handleSetArrowhead = useCallback((kind) => {
    const markerEnd = markerForArrowhead(kind)
    selectedEdgeIds.forEach(id => {
      setEdges(edges => edges.map(e => e.id === id ? { ...e, markerEnd } : e))
      onSetEdgeMarker(id, markerEnd)
    })
  }, [selectedEdgeIds, setEdges, onSetEdgeMarker])

  const handleSetLineStyle = useCallback((kind) => {
    const styleOverride = styleForLineStyle(kind)
    selectedEdgeIds.forEach(id => {
      setEdges(edges => edges.map(e => e.id === id ? { ...e, style: { ...e.style, ...styleOverride } } : e))
      onSetEdgeStyle(id, styleOverride)
    })
  }, [selectedEdgeIds, setEdges, onSetEdgeStyle])

  const handleBumpFont = useCallback((delta) => {
    selectedTextNodeIds.forEach(id => {
      setNodes(ns => ns.map(n => {
        if (n.id !== id) return n
        const next = Math.min(FONT_MAX, Math.max(FONT_MIN, (n.data.fontSize ?? FONT_DEFAULT) + delta))
        return { ...n, data: { ...n.data, fontSize: next } }
      }))
      onBumpTextFont?.(id, delta)
    })
  }, [selectedTextNodeIds, setNodes, onBumpTextFont])

  const handleSetColor = useCallback((color) => {
    selectedTextNodeIds.forEach(id => {
      setNodes(ns => ns.map(n => n.id === id ? { ...n, data: { ...n.data, color } } : n))
      onSetTextColor?.(id, color)
    })
  }, [selectedTextNodeIds, setNodes, onSetTextColor])

  const injectCallbacks = useCallback((nodes, { onLabelCommit, onTextCommit }) => {
    return nodes.map(n => ({
      ...n,
      data: {
        ...n.data,
        editMode: true,
        onLabelCommit,
        onCommit: n.type === 'text' ? onTextCommit : undefined,
      },
    }))
  }, [])

  return {
    activeTool,
    setActiveTool,
    selectedNodeIds,
    selectedEdgeIds,
    selectedTextNodeIds,
    selectionRef,
    hasTextSelection: selectedTextNodeIds.length > 0,
    onConnect,
    onNodesDelete,
    onEdgesDelete,
    onNodeDragStop,
    onSelectionChange,
    handleAddText,
    handleDelete,
    handleSetArrowhead,
    handleSetLineStyle,
    handleBumpFont,
    handleSetColor,
    injectCallbacks,
  }
}
