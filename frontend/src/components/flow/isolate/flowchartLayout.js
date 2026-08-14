import { measure, NODE_W, NODE_H, GAP_Y } from './flowchartMeasure'
import { processSequence } from './flowchartPlace'
import { elbow, dropElbow, bypassElbow, nextId } from './flowchartWire'
import { shapeFor } from './flowchartStyles'

export function layout(steps, name = 'start', maxWidth) {
  const ctx = { nodes: [], edges: [], nextId: 0, pendingEnd: [] }
  const list = steps ?? []
  const bodySize = measure(list)
  const contentWidth = Math.max(bodySize.width, NODE_W)
  const centerX = contentWidth / 2

  const startId = nextId(ctx, 'start')
  ctx.nodes.push({ id: startId, x: centerX - NODE_W / 2, y: 0, w: NODE_W, h: NODE_H, kind: 'start', label: name, shape: shapeFor('start') })
  const startExit = { x: centerX, y: NODE_H }

  const bodyResult = processSequence(list, centerX, NODE_H + GAP_Y, ctx, 'END')
  if (bodyResult.entry) {
    const geo = elbow(startExit.x, startExit.y, bodyResult.entry.x, bodyResult.entry.y)
    ctx.edges.push({ id: nextId(ctx, 'e'), path: geo.path, className: 'rf-flow-edge' })
  } else {
    ctx.pendingEnd.push({ from: startExit })
  }

  resolveEndNode(ctx, centerX)

  return {
    nodes: ctx.nodes,
    edges: ctx.edges,
    width: Math.max(0, ...ctx.nodes.map(n => n.x + n.w)),
    height: Math.max(0, ...ctx.nodes.map(n => n.y + n.h)),
  }
}

function resolveEndNode(ctx, centerX) {
  if (ctx.pendingEnd.length === 0) return
  const nodeBottoms = ctx.nodes.map(n => n.y + n.h)
  const clearBottoms = ctx.pendingEnd.filter(p => p.clear).map(p => p.clear.clearY)
  const lowest = Math.max(...nodeBottoms, ...clearBottoms)
  const endX = centerX - NODE_W / 2
  const endY = lowest + GAP_Y
  const endId = nextId(ctx, 'end')
  ctx.nodes.push({ id: endId, x: endX, y: endY, w: NODE_W, h: NODE_H, kind: 'end', label: 'end', shape: shapeFor('end') })
  const endEntry = { x: centerX, y: endY }

  for (const pending of ctx.pendingEnd) {
    let geo
    if (pending.bypassArmX !== undefined) {
      geo = bypassElbow(pending.from.x, pending.from.y, pending.bypassArmX, pending.clear.clearY, endEntry.x, endEntry.y)
    } else if (pending.clear) {
      geo = dropElbow(pending.from.x, pending.from.y, pending.clear.clearY, endEntry.x, endEntry.y)
    } else {
      geo = elbow(pending.from.x, pending.from.y, endEntry.x, endEntry.y)
    }
    const edge = { id: nextId(ctx, 'e'), path: geo.path, className: 'rf-flow-edge' }
    if (pending.label) Object.assign(edge, { label: pending.label, labelX: geo.midX, labelY: geo.midY })
    ctx.edges.push(edge)
  }
}
