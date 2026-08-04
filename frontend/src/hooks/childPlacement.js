import { scaleOf } from '../components/flow/depthScale'
import { pushBelow, spaceSiblings } from './expansionBoxes'

const MAX_BOX_DEPTH = 2
const RUN_GUTTER = 24
const MIN_ROW_SCALE = 1.3

function isRunMember(child, soloLinear) {
  return soloLinear || child.payload?.data?.shape === 'pipeline'
}

function runStepFor(geometry) {
  const rect = geometry?.rect?.height ?? 0
  const pipeline = geometry?.pipeline?.height ?? 0
  return Math.max(rect, pipeline, 1) + RUN_GUTTER
}

function placeNode(child, position, scale, depth, ctx) {
  const { placed, order, expanded } = ctx
  const node = { ...child.payload, scale, depth, position }
  placed.set(child.id, node)
  order.push(node)
  const nested = expanded.has(child.id) ? placeChildren(node, ctx, depth + 1) : []
  return { node, members: [node, ...nested] }
}

function placeRun(run, parent, ctx, depth, rowStep, geometry) {
  const step = parent.scale ?? 1
  const runStep = runStepFor(geometry)
  for (let i = 0; i + 1 < run.length; i += 1) {
    ctx.chainPairs?.add(`${run[i].id} ${run[i + 1].id}`)
  }
  return run.map((child, index) => placeNode(
    child,
    { x: parent.position.x, y: parent.position.y + Math.round((index + 1) * runStep * rowStep) },
    step,
    depth,
    ctx,
  ))
}

function placeGrid(child, parent, ctx, depth, step, rowStep) {
  return placeNode(
    child,
    {
      x: Math.round(parent.position.x + child.dx * step),
      y: Math.round(parent.position.y + child.dy * rowStep),
    },
    scaleOf(depth),
    depth,
    ctx,
  )
}

export function placeChildren(parent, ctx, depth = 1) {
  const { hiddenById, placed, order, boxes, geometry } = ctx
  const pending = (parent.data?.hiddenChildren ?? [])
    .filter(c => !placed.has(c.id) && hiddenById.has(c.id))
    .map(c => ({ ...c, payload: hiddenById.get(c.id) }))
  if (!pending.length) return []
  const soloLinear = pending.length === 1 && pending[0].payload?.data?.linear
  const step = parent.scale ?? 1
  const rowStep = Math.max(step, MIN_ROW_SCALE)
  const blockHeight = Math.round(Math.max(...pending.map(c => c.dy)) * rowStep)
  pushBelow(order, parent.position.y, blockHeight)

  const groups = []
  let index = 0
  while (index < pending.length) {
    if (isRunMember(pending[index], soloLinear)) {
      const run = []
      while (index < pending.length && isRunMember(pending[index], soloLinear)) {
        run.push(pending[index])
        index += 1
      }
      if (run.length < 2 && !soloLinear) {
        groups.push(placeGrid(run[0], parent, ctx, depth, step, rowStep))
        continue
      }
      const runPlacements = placeRun(run, parent, ctx, depth, rowStep, geometry)
      groups.push({
        node: runPlacements[0].node,
        members: runPlacements.flatMap(placement => placement.members),
      })
    } else {
      groups.push(placeGrid(pending[index], parent, ctx, depth, step, rowStep))
      index += 1
    }
  }

  spaceSiblings(groups, geometry)
  const subtree = groups.flatMap(g => g.members)
  if (depth <= MAX_BOX_DEPTH) {
    boxes.push({ ownerId: parent.id, kind: parent.kind, members: subtree.map(n => n.id), scale: step })
  }
  return subtree
}
