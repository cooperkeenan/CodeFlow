import { KIND_ACCENT } from '../flow/styles'
import { NARRATION_HEIGHT } from './NarrationPanel'

const RAIL_LEFT = 20
const RAIL_WIDTH = 3
const SEGMENT_GAP = 6
const CONTROLS_CLEARANCE = 64
const ACCENT = KIND_ACCENT.card

const TRACK = {
  future: 'rgba(255,255,255,0.06)',
  done: 'rgba(255,255,255,0.18)',
  current: ACCENT + '33',
}

function Segment({ chapter, state, position }) {
  const total = chapter.stepIds?.length || 1
  const fraction = state === 'done' ? 1 : state === 'current' ? Math.min(1, position / total) : 0
  return (
    <div
      title={`Act ${chapter.number} — ${chapter.title}`}
      style={{
        flex: total,
        minHeight: 0,
        position: 'relative',
        borderRadius: RAIL_WIDTH,
        background: TRACK[state],
        overflow: 'hidden',
      }}
    >
      {state === 'current' && (
        <div
          style={{
            position: 'absolute', left: 0, right: 0, top: 0,
            height: `${fraction * 100}%`,
            background: ACCENT,
            borderRadius: RAIL_WIDTH,
            transition: 'height 420ms cubic-bezier(.4,0,.2,1)',
          }}
        />
      )}
    </div>
  )
}

export default function ChapterRail({ chapters, currentChapterId, currentPosition }) {
  if (!chapters?.length) return null
  const currentIndex = chapters.findIndex(c => c.id === currentChapterId)
  return (
    <div
      style={{
        position: 'absolute',
        left: RAIL_LEFT,
        top: 20,
        bottom: NARRATION_HEIGHT + 16 + CONTROLS_CLEARANCE,
        width: RAIL_WIDTH,
        zIndex: 7,
        display: 'flex',
        flexDirection: 'column',
        gap: SEGMENT_GAP,
        pointerEvents: 'none',
        opacity: 0.85,
      }}
    >
      {chapters.map((chapter, index) => (
        <Segment
          key={chapter.id}
          chapter={chapter}
          position={index === currentIndex ? currentPosition : 0}
          state={index === currentIndex ? 'current' : index < currentIndex ? 'done' : 'future'}
        />
      ))}
    </div>
  )
}
