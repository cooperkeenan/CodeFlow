import { request } from './client'

export const explainNode = (repo, nodeId) =>
  request(`/repomaps/${repo}/explain`, { method: 'POST', body: JSON.stringify({ node_id: nodeId }) })
