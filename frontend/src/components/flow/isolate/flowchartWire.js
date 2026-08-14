import { GAP_Y } from './flowchartMeasure'

export function nextId(ctx, prefix) {
  ctx.nextId += 1
  return `${prefix}-${ctx.nextId}`
}

export function elbow(x1, y1, x2, y2) {
  const my = y1 + (y2 - y1) / 2
  const midX = x1 + (x2 - x1) / 2
  return { path: `M ${x1},${y1} V ${my} H ${x2} V ${y2}`, midX, midY: my }
}

export function dropElbow(x1, y1, clearY, x2, y2) {
  return { path: `M ${x1},${y1} V ${clearY} H ${x2} V ${y2}`, midX: x2, midY: clearY }
}

export function bypassElbow(x1, y1, armX, clearY, x2, y2) {
  const my1 = y1 + GAP_Y / 2
  return {
    path: `M ${x1},${y1} V ${my1} H ${armX} V ${clearY} H ${x2} V ${y2}`,
    midX: armX,
    midY: clearY,
  }
}

function backElbow(x1, y1, to) {
  const path = `M ${x1},${y1} V ${to.dropY} H ${to.channelX} V ${to.y} H ${to.x}`
  return { path, midX: to.channelX, midY: to.dropY }
}

function geometryFor(from, to) {
  if (to.clear) return dropElbow(from.x, from.y, to.clear.clearY, to.x, to.y)
  if (to.back) return backElbow(from.x, from.y, to)
  return elbow(from.x, from.y, to.x, to.y)
}

export function wire(ctx, from, to, label) {
  if (!to) return
  if (to === 'END' || to.end) {
    ctx.pendingEnd.push({ from, label, clear: to === 'END' ? undefined : to.clear })
    return
  }
  const geo = geometryFor(from, to)
  const edge = { id: nextId(ctx, 'e'), path: geo.path, className: 'rf-flow-edge' }
  if (label) Object.assign(edge, { label, labelX: geo.midX, labelY: geo.midY })
  ctx.edges.push(edge)
}

export function wireBypass(ctx, bottomPort, armX, clearedSuccessor, label) {
  if (!clearedSuccessor) return
  if (clearedSuccessor === 'END' || clearedSuccessor.end) {
    ctx.pendingEnd.push({ from: bottomPort, label, bypassArmX: armX, clear: clearedSuccessor.clear })
    return
  }
  const { clearY } = clearedSuccessor.clear
  const geo = bypassElbow(bottomPort.x, bottomPort.y, armX, clearY, clearedSuccessor.x, clearedSuccessor.y)
  const edge = { id: nextId(ctx, 'e'), path: geo.path, className: 'rf-flow-edge' }
  if (label) Object.assign(edge, { label, labelX: geo.midX, labelY: geo.midY })
  ctx.edges.push(edge)
}
