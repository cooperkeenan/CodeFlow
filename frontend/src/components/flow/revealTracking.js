const STAGGER_STEP_MS = 20
const OUTLINE_BASE_MS = 130
const OUTLINE_DUR_MS = 200
const TEXT_DUR_MS = 140
const BOX_MARGIN_MS = 30
const TEXT_BASE_MS = OUTLINE_BASE_MS + OUTLINE_DUR_MS

export const REVEAL_WINDOW_MS = 900

function boxIdsFor(revealTrigger, ids) {
  const owners = new Set(ids)
  if (revealTrigger?.parentId) owners.add(revealTrigger.parentId)
  return new Set([...owners].map(id => `box:${id}`))
}

export function revealedIdsFrom(revealTrigger) {
  if (!revealTrigger || revealTrigger.fit || !revealTrigger.childIds?.length) return null
  return new Set(revealTrigger.childIds)
}

export function withRevealedNodes(rfNodes, revealTrigger) {
  const ids = revealedIdsFrom(revealTrigger)
  if (!ids) return rfNodes
  const boxIds = boxIdsFor(revealTrigger, ids)
  const lastStagger = STAGGER_STEP_MS * (ids.size - 1)
  const revealBoxDelayMs = TEXT_BASE_MS + lastStagger + TEXT_DUR_MS + BOX_MARGIN_MS
  let i = 0
  return rfNodes.map(n => {
    if (boxIds.has(n.id)) return { ...n, data: { ...n.data, revealBacking: true, revealBoxDelayMs } }
    if (!ids.has(n.id)) return n
    const revealIndex = i
    i += 1
    return {
      ...n,
      data: {
        ...n.data,
        justRevealed: true,
        revealOutlineDelayMs: OUTLINE_BASE_MS + revealIndex * STAGGER_STEP_MS,
        revealTextDelayMs: TEXT_BASE_MS + revealIndex * STAGGER_STEP_MS,
      },
    }
  })
}

export function withRevealedEdges(rfEdges, revealTrigger) {
  const ids = revealedIdsFrom(revealTrigger)
  if (!ids) return rfEdges
  let i = 0
  return rfEdges.map(e => {
    if (!ids.has(e.target)) return e
    const revealIndex = i
    i += 1
    return { ...e, data: { ...e.data, justRevealed: true, revealEdgeDelayMs: revealIndex * STAGGER_STEP_MS } }
  })
}
