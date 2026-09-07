const PATH_PARAM = /<(?:[^:>]+:)?([^>]+)>/g
const STATUS_CODE = /^\d{3}$/

const SCALARS = ['string', 'integer', 'number', 'boolean', 'array', 'object']
const ALIASES = { int: 'integer', float: 'number', bool: 'boolean', str: 'string' }

function normalisePath(path) {
  const p = String(path || '/').split('?')[0].replace(PATH_PARAM, '{$1}')
  return p.startsWith('/') ? p : `/${p}`
}

function parseJson(text) {
  if (typeof text !== 'string' || !text.trim()) return null
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

function schemaFor(type) {
  const t = String(type || '').toLowerCase().trim()
  if (SCALARS.includes(t)) return t === 'array' ? { type: 'array', items: {} } : { type: t }
  if (ALIASES[t]) return { type: ALIASES[t] }
  if (t === 'list') return { type: 'array', items: {} }
  if (t === 'dict') return { type: 'object' }
  return t ? { type: 'string', description: type } : { type: 'string' }
}

function parameters(params) {
  return params
    .filter(p => p.location !== 'body')
    .map(p => ({
      name: p.name,
      in: p.location || 'query',
      required: p.location === 'path' ? true : Boolean(p.required),
      description: p.description || undefined,
      schema: schemaFor(p.type),
    }))
}

function requestBody(contract) {
  const bodyParams = (contract.params || []).filter(p => p.location === 'body')
  const example = parseJson(contract.request_body)
  if (!bodyParams.length && !example && !contract.request_body) return undefined
  if (!bodyParams.length) {
    const schema = { type: 'object', description: contract.request_body || undefined }
    return { content: { 'application/json': { schema, example: example || undefined } } }
  }
  const properties = {}
  const required = []
  bodyParams.forEach(p => {
    properties[p.name] = { ...schemaFor(p.type), description: p.description || undefined }
    if (p.required) required.push(p.name)
  })
  const schema = { type: 'object', properties, required: required.length ? required : undefined }
  return {
    required: required.length > 0,
    content: { 'application/json': { schema, example: example || undefined } },
  }
}

function responses(contract) {
  const out = {}
  ;(contract.responses || []).forEach(r => {
    const code = STATUS_CODE.test(String(r.status)) ? String(r.status) : 'default'
    const example = parseJson(r.shape)
    const trailer = !example && r.shape ? ` — ${r.shape}` : ''
    out[code] = { description: `${r.description || ''}${trailer}`.trim() || String(r.status) }
    if (example) out[code].content = { 'application/json': { example } }
  })
  const ok = Object.keys(out).find(code => code.startsWith('2'))
  const bodyExample = parseJson(contract.example_response)
  if (ok && bodyExample && !out[ok].content) {
    out[ok].content = { 'application/json': { example: bodyExample } }
  }
  if (!Object.keys(out).length) out.default = { description: 'No documented response.' }
  return out
}

function fenced(title, value) {
  return value ? `**${title}**\n\n\`\`\`\n${value}\n\`\`\`` : ''
}

function describe(contract, summary) {
  return [
    contract.summary === summary ? '' : contract.summary,
    contract.auth ? `**Auth:** ${contract.auth}` : '',
    fenced('Example request', contract.example_request),
    parseJson(contract.example_response) ? '' : fenced('Example response', contract.example_response),
  ]
    .filter(Boolean)
    .join('\n\n')
}

function operationId(method, path) {
  return `${method}_${path}`.replace(/[^A-Za-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
}

function operation(contract, title) {
  const method = String(contract.method || 'GET').toLowerCase()
  const path = normalisePath(contract.path)
  const params = parameters(contract.params || [])
  const summary = title || contract.name || contract.summary || path
  const op = {
    operationId: operationId(method, path),
    summary,
    description: describe(contract, summary) || undefined,
    parameters: params.length ? params : undefined,
    responses: responses(contract),
  }
  const body = requestBody(contract)
  if (body && method !== 'get' && method !== 'head') op.requestBody = body
  return { method, path, op }
}

export function contractsToOpenApi(contracts, { title, baseUrl = 'http://localhost:8000' } = {}) {
  const list = (contracts || []).filter(Boolean)
  const paths = {}
  list.forEach(contract => {
    const { method, path, op } = operation(contract, list.length === 1 ? title : '')
    paths[path] = { ...(paths[path] || {}), [method]: op }
  })
  const first = list[0]
  const fallback = first
    ? `${String(first.method || 'GET').toUpperCase()} ${normalisePath(first.path)}`
    : 'API'
  return {
    openapi: '3.1.0',
    info: { title: title || fallback, version: '1.0.0' },
    servers: [{ url: '{baseUrl}', variables: { baseUrl: { default: baseUrl } } }],
    paths,
  }
}

export function contractsToOpenApiText(contracts, options) {
  return JSON.stringify(contractsToOpenApi(contracts, options), null, 2)
}
