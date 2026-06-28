import { request } from './client'

export const runAnalysis = (endpoint, body = null) =>
  request(endpoint, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  })