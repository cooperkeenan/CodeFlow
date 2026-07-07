import { request } from './client'

export const fetchCode = (repo, path) =>
  request(`/code?repo=${encodeURIComponent(repo)}&path=${encodeURIComponent(path)}`)
