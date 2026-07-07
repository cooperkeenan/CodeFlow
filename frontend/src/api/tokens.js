import { request } from './client'

export const createToken = (name) =>
  request('/tokens', { method: 'POST', body: JSON.stringify({ name }) })

export const listTokens = () => request('/tokens')

export const revokeToken = (id) => request(`/tokens/${id}`, { method: 'DELETE' })
