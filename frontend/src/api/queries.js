import { getFlowGraph } from './flow'
import { getRepoHome, listRepoMaps } from './repomaps'
import { getDiagramEdits } from './diagrams'
import { explainNode } from './explain'

export const flowQueryKey = (repo, fixtureUrl, entry, helper) => [
  'flow',
  repo,
  fixtureUrl ?? null,
  helper ? `helper:${helper}` : entry ?? 'full',
]

export const flowQueryFn = (repo, fixtureUrl, entry, helper) => () =>
  fixtureUrl ? fetch(fixtureUrl).then(res => res.json()) : getFlowGraph(repo, { entry, helper })

export const repoHomeQueryKey = (repo, fixtureUrl) => ['repo-home', repo, fixtureUrl ?? null]

export const repoHomeQueryFn = (repo, fixtureUrl) => () =>
  fixtureUrl ? fetch(fixtureUrl).then(res => res.json()) : getRepoHome(repo)

export const diagramEditsQueryKey = (repo) => ['diagram-edits', repo]

export const diagramEditsQueryFn = (repo) => () => getDiagramEdits(repo)

export const repoMapListQueryKey = () => ['repo-map-list']

export const repoMapListQueryFn = () => () => listRepoMaps()

export const explainQueryKey = (repo, nodeId) => ['explain', repo, nodeId]

export const explainQueryFn = (repo, nodeId) => () => explainNode(repo, nodeId)
