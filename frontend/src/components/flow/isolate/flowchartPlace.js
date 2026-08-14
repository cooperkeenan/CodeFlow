import { measure, measureStep, armColumnSize, NODE_W, NODE_H, DIAMOND_W, DIAMOND_H, GAP_X, GAP_Y, LOOP_BACK_PAD, CHANNEL_PAD } from './flowchartMeasure'
import { shapeFor } from './flowchartStyles'
import { wire, wireBypass, nextId } from './flowchartWire'

const TERMINAL_KINDS = new Set(['return', 'raise'])

function entryPoint(step, box) {
  if (step.kind === 'loop') return { x: box.x + NODE_W / 2, y: box.y }
  return { x: box.x + box.w / 2, y: box.y }
}

export function processSequence(steps, centerX, y, ctx, successor) {
  if (!steps || steps.length === 0) return { entry: null }
  const sizes = steps.map(measureStep)
  const boxes = []
  let cursorY = y
  for (const size of sizes) {
    boxes.push({ x: centerX - size.width / 2, y: cursorY, w: size.width, h: size.height })
    cursorY += size.height + GAP_Y
  }
  const entries = boxes.map((box, index) => entryPoint(steps[index], box))
  steps.forEach((step, index) => {
    const isLast = index === steps.length - 1
    placeStep(step, boxes[index], ctx, isLast ? successor : entries[index + 1])
  })
  return { entry: entries[0] }
}

function placeStep(step, box, ctx, successor) {
  if (step.kind === 'decision') return placeDecision(step, box, ctx, successor)
  if (step.kind === 'loop') return placeLoop(step, box, ctx, successor)
  return placeLeaf(step, box, ctx, successor)
}

function placeLeaf(step, box, ctx, successor) {
  const id = nextId(ctx, step.kind)
  ctx.nodes.push({ id, x: box.x, y: box.y, w: box.w, h: box.h, kind: step.kind, label: step.label, shape: shapeFor(step.kind), line: step.line, fqn: step.fqn, raw: step.raw, llmLabel: step.llm_label })
  if (TERMINAL_KINDS.has(step.kind)) return
  const exit = { x: box.x + box.w / 2, y: box.y + box.h }
  wire(ctx, exit, successor)
}

function wrapClear(successor, clearY) {
  if (!successor) return successor
  if (successor === 'END') return { end: true, clear: { clearY } }
  const merged = successor.clear ? Math.max(successor.clear.clearY, clearY) : clearY
  return { ...successor, clear: { clearY: merged } }
}

function placeDecision(step, box, ctx, successor) {
  const arms = step.arms ?? []
  const id = nextId(ctx, 'decision')
  const dX = box.x + (box.w - DIAMOND_W) / 2
  ctx.nodes.push({ id, x: dX, y: box.y, w: DIAMOND_W, h: DIAMOND_H, kind: 'decision', label: step.label, shape: 'diamond', line: step.line, fqn: step.fqn, raw: step.raw, llmLabel: step.llm_label })
  const bottomPort = { x: dX + DIAMOND_W / 2, y: box.y + DIAMOND_H }
  const armsY = bottomPort.y + GAP_Y
  const armSizes = arms.map(armColumnSize)
  const clearY = armsY + Math.max(0, ...armSizes.map(size => size.height))
  const totalArmWidth = armSizes.reduce((sum, size) => sum + size.width, 0) + GAP_X * (armSizes.length - 1)
  let cursorX = box.x + (box.w - totalArmWidth) / 2
  arms.forEach((arm, index) => {
    const armW = armSizes[index].width
    const armCenterX = cursorX + armW / 2
    const clearedSuccessor = wrapClear(successor, clearY)
    const armResult = processSequence(arm.steps, armCenterX, armsY, ctx, clearedSuccessor)
    if (armResult.entry) {
      wire(ctx, bottomPort, armResult.entry, arm.label)
    } else {
      wireBypass(ctx, bottomPort, armCenterX, clearedSuccessor, arm.label)
    }
    cursorX += armW + GAP_X
  })
}

function placeLoop(step, box, ctx, successor) {
  const id = nextId(ctx, 'loop')
  const bodySteps = step.body ?? []
  const bodySize = measure(bodySteps)
  const loopX = box.x
  const loopY = box.y
  ctx.nodes.push({ id, x: loopX, y: loopY, w: NODE_W, h: NODE_H, kind: 'loop', label: step.label, shape: 'rect', line: step.line, fqn: step.fqn, raw: step.raw, llmLabel: step.llm_label })

  const bodyCenterX = loopX + NODE_W + GAP_X + bodySize.width / 2
  const lateralPort = { x: loopX + NODE_W, y: loopY }
  const bottomPort = { x: loopX + NODE_W / 2, y: loopY + NODE_H }

  const bodyBottomY = loopY + Math.max(bodySize.height, NODE_H)
  const channelX = box.x + box.w - CHANNEL_PAD / 2
  const dropY = bodyBottomY + LOOP_BACK_PAD / 2
  const backPort = { x: lateralPort.x, y: lateralPort.y, back: true, dropY, channelX }

  const bodyResult = processSequence(bodySteps, bodyCenterX, loopY, ctx, backPort)
  if (bodyResult.entry) wire(ctx, lateralPort, bodyResult.entry)
  wire(ctx, bottomPort, wrapClear(successor, box.y + box.h))
}
