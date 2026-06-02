import { stackTemplate } from './stackTemplate'

export function pipelineTemplate(members) {
  const base = stackTemplate(members)
  const edges = []
  for (let i = 0; i < members.length - 1; i += 1) {
    edges.push({ source: members[i].name, target: members[i + 1].name })
  }
  return { ...base, edges }
}
