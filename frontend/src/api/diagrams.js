import { request } from './client'

export const getDiagramEdits = (repo) =>
  request(`/diagram/edits?repo=${encodeURIComponent(repo)}`)

export const saveDiagramEdits = (repo, edits) =>
  request(`/diagram/edits?repo=${encodeURIComponent(repo)}`, {
    method: 'PUT', body: JSON.stringify({ edits }),
  })
