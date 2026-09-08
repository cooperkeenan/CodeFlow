import { request } from './client'

export const runLocalCi = (path) =>
  request('/ci/analyse/local', {
    method: 'POST',
    body: JSON.stringify({ path: path || null }),
  })

export const runGithubCi = (repoName) =>
  request('/ci/analyse/github', {
    method: 'POST',
    body: JSON.stringify({ repo_name: repoName }),
  })

export const getProgress = (since = 0) => request(`/ci/progress?since=${since}`)
