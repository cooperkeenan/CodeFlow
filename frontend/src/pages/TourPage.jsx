import { useEffect, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useFlowGraph } from '../hooks/useFlowGraph'
import { useGraphTransform } from '../hooks/useGraphTransform'
import { useTourPlayback } from '../hooks/useTourPlayback'
import FlowCanvas from '../components/flow/FlowCanvas'
import { CANVAS, BORDER } from '../components/flow/styles'
import TourCamera from '../components/tour/TourCamera'
import NarrationPanel, { NARRATION_HEIGHT } from '../components/tour/NarrationPanel'
import TourControls from '../components/tour/TourControls'
import ChapterRail from '../components/tour/ChapterRail'

const MONO = 'IBM Plex Mono, monospace'
const TOUR_URL = '/tour/codeflow_tour.json'
const MUTED = { fontFamily: MONO, fontSize: 12, color: 'rgba(255,255,255,0.38)', padding: '1rem' }

const VIGNETTE = {
  position: 'absolute', inset: 0, zIndex: 6, pointerEvents: 'none',
  background: 'radial-gradient(ellipse at 50% 40%, rgba(0,0,0,0) 38%, rgba(0,0,0,0.3) 100%)',
}

export default function TourPage() {
  const { payload, loading, error } = useFlowGraph(null, TOUR_URL)
  const view = payload?.view ?? payload
  const steps = payload?.steps ?? []
  const chapters = payload?.chapters ?? []
  const tour = useTourPlayback(steps)
  const navigate = useNavigate()
  const { nodes, edges } = useGraphTransform(view, undefined, view?.node_geometry)
  const step = tour.step

  const focusIds = useMemo(() => step?.focus ?? [], [step])
  const focusSet = useMemo(() => new Set(focusIds), [focusIds])
  const adjacentSet = useMemo(() => {
    const out = new Set()
    for (const offset of [-1, 1]) {
      const neighbour = steps[tour.index + offset]
      if (neighbour) out.add(neighbour.anchor)
    }
    return out
  }, [steps, tour.index])
  const packetSet = useMemo(() => new Set(step?.packets ?? []), [step])

  const cardIds = useMemo(() => new Set(nodes.filter(n => n.type === 'card').map(n => n.id)), [nodes])
  const stepAnchorById = useMemo(() => {
    const map = new Map()
    for (const s of steps) map.set(s.id, s.anchor)
    return map
  }, [steps])
  const chapterSpineIds = useMemo(() => {
    const chapter = chapters.find(c => c.id === step?.chapter)
    const out = new Set()
    for (const id of chapter?.stepIds ?? []) out.add(stepAnchorById.get(id) ?? id)
    return out
  }, [chapters, step, stepAnchorById])
  const visibleIds = useMemo(() => {
    const out = new Set([...focusIds, ...adjacentSet, ...chapterSpineIds])
    for (const id of out) {
      if (cardIds.has(id) && !focusSet.has(id)) out.delete(id)
    }
    return out
  }, [focusIds, adjacentSet, chapterSpineIds, cardIds, focusSet])

  const prevFocusRef = useRef(new Set())
  const enteringIds = useMemo(() => {
    const prev = prevFocusRef.current
    const out = new Set()
    for (const id of focusIds) if (!prev.has(id)) out.add(id)
    return out
  }, [focusIds])
  useEffect(() => {
    prevFocusRef.current = focusSet
  }, [focusSet])

  return (
    <main style={{ height: '100vh', display: 'flex', flexDirection: 'column', padding: '1.1rem 1.4rem', gap: '0.9rem', boxSizing: 'border-box' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: '1.2rem', flexWrap: 'wrap' }}>
        <button className="back" onClick={() => navigate('/')}>&larr; repos</button>
        <h1 style={{ fontFamily: MONO, fontSize: '1.25rem', fontWeight: 600, color: 'rgba(255,255,255,0.87)', margin: 0 }}>
          {payload?.page_title ?? 'CodeFlow tour'}
        </h1>
        <span style={{ fontFamily: MONO, fontSize: 11, color: 'rgba(255,255,255,0.38)' }}>
          guided tour - space to pause, arrows to step
        </span>
      </header>

      <div style={{ position: 'relative', flex: 1, minHeight: 0, border: `1px solid ${BORDER}`, borderRadius: 3, overflow: 'hidden', background: CANVAS }}>
        {error && <div style={MUTED}>failed to load tour: {error}</div>}
        {!error && loading && <div style={MUTED}>loading tour…</div>}
        {!error && !loading && nodes.length > 0 && (
          <>
            <FlowCanvas
              nodes={nodes}
              edges={edges}
              selectedId={null}
              onNodeClick={() => {}}
              onPaneClick={() => {}}
              revealTrigger={null}
              focusIds={focusSet}
              adjacentIds={adjacentSet}
              packetIds={packetSet}
              visibleIds={visibleIds}
              enteringIds={enteringIds}
              suppressSelfLabels
              stepKey={tour.index}
              chrome={{ controls: false, minimap: false }}
            >
              <TourCamera
                focusIds={focusIds}
                tick={tour.index}
                bottomInset={NARRATION_HEIGHT}
                shot={step?.shot}
              />
            </FlowCanvas>
            <div style={VIGNETTE} />
            <ChapterRail
              chapters={chapters}
              currentChapterId={step?.chapter}
              currentPosition={step?.chapterPosition}
            />
            <NarrationPanel
              step={step}
              index={tour.index}
              count={tour.count}
              repoUrl={payload?.repo_url}
              chapters={chapters}
            />
            <TourControls
              index={tour.index}
              count={tour.count}
              playing={tour.playing}
              onPrev={tour.prev}
              onNext={tour.next}
              onToggle={tour.toggle}
              onRestart={tour.restart}
              onGoto={tour.goto}
              bottom={NARRATION_HEIGHT + 16}
              dwellMs={step?.dwellMs}
            />
          </>
        )}
      </div>
    </main>
  )
}
