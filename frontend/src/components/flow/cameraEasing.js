const P1X = 0.5
const P1Y = 0
const P2X = 0.2
const P2Y = 1

function bezier(t, a, b) {
  const mt = 1 - t
  return 3 * mt * mt * t * a + 3 * mt * t * t * b + t * t * t
}

function inverseCubicInOut(eased) {
  if (eased <= 0) return 0
  if (eased >= 1) return 1
  if (eased < 0.5) return Math.cbrt(eased / 4)
  return (2 - Math.cbrt(2 * (1 - eased))) / 2
}

function solveT(x) {
  let lo = 0
  let hi = 1
  for (let i = 0; i < 24; i += 1) {
    const mid = (lo + hi) / 2
    if (bezier(mid, P1X, P2X) < x) lo = mid
    else hi = mid
  }
  return (lo + hi) / 2
}

export function cssFrameProgress(easedT) {
  return bezier(solveT(inverseCubicInOut(easedT)), P1Y, P2Y)
}
