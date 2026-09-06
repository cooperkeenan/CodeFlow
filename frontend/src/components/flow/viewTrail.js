const SEGMENT_SEP = ','

export function currentViewKey(entry, helper) {
  if (helper) return { kind: 'helper', value: helper }
  if (entry) return { kind: 'entry', value: entry }
  return null
}

export function parseTrail(fromParam) {
  if (!fromParam) return []
  return fromParam.split(SEGMENT_SEP).filter(Boolean).map(segment => {
    const separatorIndex = segment.indexOf(':')
    return {
      kind: segment.slice(0, separatorIndex),
      value: decodeURIComponent(segment.slice(separatorIndex + 1)),
    }
  })
}

function serializeTrail(trail) {
  return trail.map(({ kind, value }) => `${kind}:${encodeURIComponent(value)}`).join(SEGMENT_SEP)
}

export function viewUrl(pathname, kind, value, trail) {
  const query = new URLSearchParams()
  query.set(kind, value)
  const fromParam = serializeTrail(trail)
  if (fromParam) query.set('from', fromParam)
  return `${pathname}?${query.toString()}`
}

export function appendCurrentView(trail, entry, helper) {
  const current = currentViewKey(entry, helper)
  return current ? [...trail, current] : trail
}
