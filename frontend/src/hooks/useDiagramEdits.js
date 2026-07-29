import { useState, useEffect, useRef, useCallback } from 'react'
import { getDiagramEdits, saveDiagramEdits } from '../api/diagrams'
import { debounce } from './debounce'
import { EMPTY_OVERLAY } from './graph/overlayReducer'
import {
  addEdgeReducer,
  deleteElementsReducer,
  setEdgeMarkerReducer,
  setEdgeStyleReducer,
  moveNodeReducer,
  setNodeLabelReducer,
  addTextNodeReducer,
  setTextNodeLabelReducer,
  bumpTextFontReducer,
  setTextColorReducer,
} from './graph/overlayReducer'

const DEBOUNCE_MS = 600

export function useDiagramEdits(repo) {
  const [editsMap, setEditsMap] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!repo) return
    setLoading(true)
    setError(null)
    getDiagramEdits(repo)
      .then(data => setEditsMap(data?.edits ?? {}))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [repo])

  const saveRef = useRef(null)
  useEffect(() => {
    saveRef.current = debounce((map) => {
      if (repo) saveDiagramEdits(repo, map).catch(() => null)
    }, DEBOUNCE_MS)
  }, [repo])

  const mutate = useCallback((viewId, reducer) => {
    setEditsMap(prev => {
      const updated = { ...prev, [viewId]: reducer(prev[viewId] ?? EMPTY_OVERLAY) }
      saveRef.current?.(updated)
      return updated
    })
  }, [])

  const overlayFor = useCallback(
    (viewId) => editsMap[viewId] ?? EMPTY_OVERLAY,
    [editsMap]
  )

  const addEdge = useCallback(
    (viewId, edge) => mutate(viewId, o => addEdgeReducer(o, edge)),
    [mutate]
  )

  const deleteElements = useCallback(
    (viewId, { nodeIds, edgeIds }) =>
      mutate(viewId, o => deleteElementsReducer(o, { nodeIds, edgeIds })),
    [mutate]
  )

  const setEdgeMarker = useCallback(
    (viewId, edgeId, markerEnd, markerStart) =>
      mutate(viewId, o => setEdgeMarkerReducer(o, edgeId, markerEnd, markerStart)),
    [mutate]
  )

  const setEdgeStyle = useCallback(
    (viewId, edgeId, style) =>
      mutate(viewId, o => setEdgeStyleReducer(o, edgeId, style)),
    [mutate]
  )

  const moveNode = useCallback(
    (viewId, nodeId, position) =>
      mutate(viewId, o => moveNodeReducer(o, nodeId, position)),
    [mutate]
  )

  const setNodeLabel = useCallback(
    (viewId, nodeId, label) =>
      mutate(viewId, o => setNodeLabelReducer(o, nodeId, label)),
    [mutate]
  )

  const addTextNode = useCallback(
    (viewId, node) => mutate(viewId, o => addTextNodeReducer(o, node)),
    [mutate]
  )

  const setTextNodeLabel = useCallback(
    (viewId, nodeId, text) =>
      mutate(viewId, o => setTextNodeLabelReducer(o, nodeId, text)),
    [mutate]
  )

  const bumpTextFont = useCallback(
    (viewId, nodeId, delta) => mutate(viewId, o => bumpTextFontReducer(o, nodeId, delta)),
    [mutate]
  )

  const setTextColor = useCallback(
    (viewId, nodeId, color) => mutate(viewId, o => setTextColorReducer(o, nodeId, color)),
    [mutate]
  )

  return {
    loading,
    error,
    overlayFor,
    addEdge,
    deleteElements,
    setEdgeMarker,
    setEdgeStyle,
    moveNode,
    setNodeLabel,
    addTextNode,
    setTextNodeLabel,
    bumpTextFont,
    setTextColor,
  }
}
