const SKIPPED_TYPES = new Set(['laneHeader', 'flowGroup'])
const SKIPPED_PREFIXES = ['endlink:', 'endcont:']

export function brainstormUrl(repo, node) {
  if (!node || SKIPPED_TYPES.has(node.type)) return null
  if (SKIPPED_PREFIXES.some(prefix => node.id?.startsWith(prefix))) return null
  const label = node.data?.fullLabel || node.data?.label
  if (!label) return null
  const oneLiner = node.data?.oneLiner ? ` ${node.data.oneLiner}` : ''
  const params = new URLSearchParams()
  if (repo) params.set('repo', repo)
  params.set('q', `How does "${label}" work?${oneLiner}`)
  return `/brainstorm?${params.toString()}`
}
