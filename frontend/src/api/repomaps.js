import { request } from './client'

export const listRepoMaps = () => request('/repomaps')

export const getRepoMap = (repo) => request(`/repomaps/${repo}`)

export const getRepoHome = (repo) => request(`/repomaps/${repo}/home`)
