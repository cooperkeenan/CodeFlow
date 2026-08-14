export const NODE_W = 168
export const NODE_H = 48
export const DIAMOND_W = 168
export const DIAMOND_H = 84
export const GAP_X = 45
export const GAP_Y = 33
export const LOOP_BACK_PAD = 30
export const CHANNEL_PAD = 24

export function measure(steps) {
  if (!steps || steps.length === 0) return { width: 0, height: 0 }
  const sizes = steps.map(measureStep)
  const width = Math.max(...sizes.map(size => size.width))
  const height = sizes.reduce((sum, size) => sum + size.height, 0) + GAP_Y * (sizes.length - 1)
  return { width, height }
}

export function measureStep(step) {
  if (step.kind === 'decision') return measureDecision(step)
  if (step.kind === 'loop') return measureLoop(step)
  return { width: NODE_W, height: NODE_H }
}

export function armColumnSize(arm) {
  const size = measure(arm.steps)
  return { width: size.width > 0 ? size.width : NODE_W / 2, height: size.height }
}

function measureDecision(step) {
  const arms = step.arms ?? []
  if (arms.length === 0) return { width: DIAMOND_W, height: DIAMOND_H }
  const armSizes = arms.map(armColumnSize)
  const totalArmWidth = armSizes.reduce((sum, size) => sum + size.width, 0) + GAP_X * (armSizes.length - 1)
  const maxArmHeight = Math.max(...armSizes.map(size => size.height))
  return { width: Math.max(DIAMOND_W, totalArmWidth), height: DIAMOND_H + GAP_Y + maxArmHeight }
}

function measureLoop(step) {
  const bodySize = measure(step.body ?? [])
  return {
    width: NODE_W + GAP_X + bodySize.width + CHANNEL_PAD,
    height: Math.max(NODE_H, bodySize.height) + LOOP_BACK_PAD,
  }
}
