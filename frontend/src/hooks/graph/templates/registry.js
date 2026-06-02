import { gridTemplate } from './gridTemplate'
import { stackTemplate } from './stackTemplate'
import { pipelineTemplate } from './pipelineTemplate'
import { hierarchyTemplate } from './hierarchyTemplate'
import { hubTemplate } from './hubTemplate'

export const TEMPLATES = {
  grid: gridTemplate,
  stack: stackTemplate,
  pipeline: pipelineTemplate,
  hierarchy: hierarchyTemplate,
  hub: hubTemplate,
}

export const resolveTemplate = (style) => TEMPLATES[style] ?? gridTemplate
