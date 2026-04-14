import { request } from './client'

export const exchangeCode = (code) =>
  request('/github/auth/callback', {
    method: 'POST',
    body: JSON.stringify({ code }),
  })

export const listRepos = (accessToken) =>
  request(`/github/repos?access_token=${accessToken}`)