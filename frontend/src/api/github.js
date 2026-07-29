import { request } from './client'
import { GITHUB_CLIENT_ID, REDIRECT_URI } from '../constants'

export const startGithubOAuth = () => {
  window.location.href =
    `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=repo`
}

export const exchangeCode = (code) =>
  request('/github/auth/callback', {
    method: 'POST',
    body: JSON.stringify({ code }),
  })

export const listRepos = (accessToken) =>
  request(`/github/repos?access_token=${accessToken}`)

export const listMyRepos = () => request('/github/my-repos')

export const linkGithub = (code) =>
  request('/github/link', {
    method: 'POST',
    body: JSON.stringify({ code }),
  })