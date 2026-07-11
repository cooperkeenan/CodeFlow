import { request } from './client'

export const runLocalCi = (path) =>
  request('/ci/analyse/local', {
    method: 'POST',
    body: JSON.stringify({ path: path || null }),
  })
