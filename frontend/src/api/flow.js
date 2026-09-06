import { request } from './client'

// TODO(F13): point at the real single endpoint once the server wires it.
// It must return one payload the whole page renders from, shaped as:
//   { page_title, repo, repo_url, view: { type: 'flow', nodes, edges } }
// where `view` is the render agent's RenderedView (geometry + labels) and
// `repo_url` is a blob base URL (e.g. https://github.com/owner/repo/blob/main)
// used by the provenance popover. The node `data` must also carry `backing`
// and `refs` (present on FlowNode, currently dropped by flow_emit) and edges
// their `confidence` so provenance rows and inferred-edge styling render.
export const getFlowGraph = (repo, { entry, helper } = {}) => {
  const query = helper
    ? `?helper=${encodeURIComponent(helper)}`
    : entry
      ? `?entry=${encodeURIComponent(entry)}`
      : ''
  return request(`/repomaps/${repo}/flow${query}`)
}

export const endpointSlug = (entry) => entry.replace(/[^A-Za-z0-9]+/g, '_')

export const helperSlug = (owner) => `helper_${endpointSlug(owner)}`

export const endpointFixtureUrl = (entry) => `/fixture/endpoints/${endpointSlug(entry)}.json`

export const helperFixtureUrl = (owner) => `/fixture/endpoints/${helperSlug(owner)}.json`
