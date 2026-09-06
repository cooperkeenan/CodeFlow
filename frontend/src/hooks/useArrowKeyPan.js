import { useEffect } from 'react'
import { useReactFlow } from 'reactflow'

const PAN_STEP = 60
const PAN_STEP_FAST = 240

const KEY_DELTA = {
  ArrowLeft: [1, 0],
  ArrowRight: [-1, 0],
  ArrowUp: [0, 1],
  ArrowDown: [0, -1],
}

function isTypingTarget(target) {
  if (!target) return false
  const tag = target.tagName ? target.tagName.toLowerCase() : ''
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return true
  return !!target.isContentEditable
}

export function useArrowKeyPan() {
  const { getViewport, setViewport } = useReactFlow()

  useEffect(() => {
    const onKeyDown = e => {
      const delta = KEY_DELTA[e.key]
      if (!delta || isTypingTarget(e.target)) return
      e.preventDefault()
      const step = e.shiftKey ? PAN_STEP_FAST : PAN_STEP
      const viewport = getViewport()
      setViewport({
        x: viewport.x + delta[0] * step,
        y: viewport.y + delta[1] * step,
        zoom: viewport.zoom,
      })
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [getViewport, setViewport])
}
