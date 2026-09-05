import { useCallback, useMemo, useState } from 'react'
import { buildBoxes } from './expansionBoxes'
import { placeChildren } from './childPlacement'
import { routeChainEdges } from './chainEdges'

export function useExpansion(view, showSecondary, initialIds) {
  const [expanded, setExpanded] = useState(() => new Set(initialIds ?? []))
  const [lastReveal, setLastReveal] = useState(null)

  const childIdsOf = useCallback(id => {
    const source =
      (view?.nodes ?? []).find(n => n.id === id) ?? (view?.hidden ?? []).find(n => n.id === id)
    return (source?.data?.hiddenChildren ?? []).map(c => c.id)
  }, [view])

  const revealedUnder = useCallback((id, expandedSet) => {
    const out = []
    const seen = new Set([id])
    const walk = rootId => {
      for (const childId of childIdsOf(rootId)) {
        if (seen.has(childId)) continue
        seen.add(childId)
        out.push(childId)
        if (expandedSet.has(childId)) walk(childId)
      }
    }
    walk(id)
    return out
  }, [childIdsOf])

  const toggle = useCallback(id => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
        setLastReveal(null)
      } else {
        next.add(id)
        setLastReveal({ parentId: id, childIds: revealedUnder(id, next) })
      }
      return next
    })
  }, [revealedUnder])

  const collapseAll = useCallback(() => {
    setExpanded(new Set())
    setLastReveal({ fit: true })
  }, [])

  const result = useMemo(() => {
    if (!view?.nodes) return { nodes: [], edges: [], expandableCount: 0 }
    const hiddenById = new Map((view.hidden ?? []).map(n => [n.id, n]))
    const soleChildOf = id => {
      const source = (view.nodes ?? []).find(n => n.id === id) ?? hiddenById.get(id)
      const kids = source?.data?.hiddenChildren ?? []
      return kids.length === 1 ? kids[0].id : null
    }
    const implicit = new Set()
    const walkSole = id => {
      let current = id
      while (current && !implicit.has(current)) {
        const only = soleChildOf(current)
        if (!only) return
        implicit.add(current)
        current = only
      }
    }
    for (const node of view.nodes) walkSole(node.id)
    const open = new Set([...expanded, ...implicit])
    const placed = new Map()
    const order = []
    for (const node of view.nodes) {
      const copy = { ...node, position: { ...node.position } }
      placed.set(node.id, copy)
      order.push(copy)
    }
    const boxes = []
    const chainPairs = new Set()
    const ctx = { hiddenById, placed, expanded: open, order, boxes, chainPairs, geometry: view.node_geometry }
    const roots = order
      .filter(n => open.has(n.id))
      .sort((a, b) => a.position.y - b.position.y)
    for (const node of roots) placeChildren(node, ctx)
    const boxNodes = buildBoxes(boxes, placed, view.node_geometry)
    const nodes = [
      ...boxNodes,
      ...order.map(node => ({
        ...node,
        data: {
          ...node.data,
          expandable: (node.data?.hiddenChildren ?? []).length > 1,
          expanded: open.has(node.id),
          hiddenCount: (node.data?.hiddenChildren ?? []).length,
        },
      })),
    ]
    const visible = new Set(placed.keys())
    const spliced = e => {
      const path = e.hiddenPath ?? []
      return path.length > 0 && path.every(id => visible.has(id))
    }
    const skeletonEdges = (view.edges ?? [])
      .filter(e => showSecondary || !e.secondary)
      .filter(e => !spliced(e))
    const childOf = new Set()
    for (const node of order) {
      for (const c of node.data?.hiddenChildren ?? []) childOf.add(`${node.id} ${c.id}`)
    }
    const primary = pair => childOf.has(pair) || chainPairs.has(pair)
    const revealedEdges = (view.hidden_edges ?? [])
      .filter(e => visible.has(e.source) && visible.has(e.target))
      .map(e => ({ ...e, secondary: !primary(`${e.source} ${e.target}`) }))
      .filter(e => showSecondary || !e.secondary)
    const seen = new Set()
    const merged = [...skeletonEdges, ...revealedEdges].filter(e => {
      if (seen.has(e.id)) return false
      seen.add(e.id)
      return visible.has(e.source) && visible.has(e.target)
    })
    const edges = routeChainEdges(merged, placed, expanded)
      .filter(e => visible.has(e.source) && visible.has(e.target))
      .map(e => ({
        ...e,
        scale: Math.min(placed.get(e.source)?.scale ?? 1, placed.get(e.target)?.scale ?? 1),
      }))
    const expandableCount = view.nodes.filter(
      n => (n.data?.hiddenChildren ?? []).length > 1,
    ).length
    return { nodes, edges, expandableCount }
  }, [view, expanded, showSecondary])

  return { ...result, expanded, toggle, collapseAll, lastReveal }
}
