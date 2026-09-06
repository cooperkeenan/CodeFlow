const MAX_NAME = 26

export function shortName(target) {
  const parts = target.split(/[.:]/).filter(Boolean)
  const tail = parts[parts.length - 1] ?? target
  const pair = parts.length > 1 ? `${parts[parts.length - 2]}.${tail}` : tail
  if (pair.length <= MAX_NAME) return pair
  return tail.length > MAX_NAME ? `${tail.slice(0, MAX_NAME - 1)}…` : tail
}

export function resolveEntryLabel(home, entryId) {
  const pools = [home?.endpoints, home?.entry_points]
  for (const pool of pools) {
    const hit = pool?.find(item => item.id === entryId)
    if (hit?.label) return hit.label
  }
  return null
}

export function viewLabel(kind, value, home) {
  if (kind === 'entry') return resolveEntryLabel(home, value) || shortName(value)
  return shortName(value)
}
