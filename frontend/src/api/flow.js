import { request } from './client'

// TODO(F13): point at the real single endpoint once the server wires it.
// It must return one payload the whole page renders from, shaped as:
//   { page_title, repo, repo_url, view: { type: 'flow', nodes, edges } }
// where `view` is the render agent's RenderedView (geometry + labels) and
// `repo_url` is a blob base URL (e.g. https://github.com/owner/repo/blob/main)
// used by the provenance popover. The node `data` must also carry `backing`
// and `refs` (present on FlowNode, currently dropped by flow_emit) and edges
// their `confidence` so provenance rows and inferred-edge styling render.
export const getFlowGraph = (repo) => request(`/repomaps/${repo}/flow`)
