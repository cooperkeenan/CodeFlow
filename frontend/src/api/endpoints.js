import { request } from './client'
import { endpointSlug } from './flow'

export const getEndpointDetail = (repo, entry) =>
  request(`/repomaps/${repo}/endpoint?entry=${encodeURIComponent(entry)}`)

export const endpointDetailFixtureUrl = (entry) =>
  `/fixture/endpoints/detail_${endpointSlug(entry)}.json`
