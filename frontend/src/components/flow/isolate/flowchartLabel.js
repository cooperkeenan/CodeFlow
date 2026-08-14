const RECEIVER_RE = /^(self\.|super\(\)\.)/
const CALL_KINDS = new Set(['call', 'effect'])
const SELF_STRIP_KINDS = new Set(['decision', 'return', 'raise', 'loop'])
const GETTEXT = new Set(['_', 'gettext', 'ugettext', 'gettext_lazy', 'ugettext_lazy'])
const GENERIC = new Set(['getattr', 'setattr', 'hasattr'])
const LITERAL_RE = /['"]([^'"]{1,40})/

function dropArgs(text) {
  const index = text.indexOf('(')
  return index === -1 ? text : text.slice(0, index)
}

function firstLiteral(text) {
  const index = text.indexOf('(')
  if (index === -1) return ''
  const match = LITERAL_RE.exec(text.slice(index))
  return match ? match[1].trim() : ''
}

function humanise(segment) {
  const stripped = segment.replace(/^_+/, '')
  if (stripped.length === 0) return segment
  return stripped.replace(/_/g, ' ')
}

function displayCallLabel(text) {
  const bare = text.replace(RECEIVER_RE, '')
  const callee = dropArgs(bare)
  const last = callee.split('.').pop()
  if (GETTEXT.has(last)) {
    const literal = firstLiteral(text)
    return literal ? `"${literal}"` : callee
  }
  if (GENERIC.has(last)) {
    const literal = firstLiteral(text)
    return literal ? `${last} ${literal}` : callee
  }
  return callee.includes('.') ? callee : humanise(callee)
}

function stripSelf(text) {
  return text.replace(/self\./g, '')
}

export function displayLabel(label, kind) {
  const text = label ?? ''
  if (CALL_KINDS.has(kind)) return displayCallLabel(text)
  if (SELF_STRIP_KINDS.has(kind)) return stripSelf(text)
  return text
}
