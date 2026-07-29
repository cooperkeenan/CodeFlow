import CustomNode from './CustomNode'
import ModuleGroupNode from './nodes/ModuleGroupNode'
import ZoneGroupNode from './nodes/ZoneGroupNode'
import ClusterGroupNode from './nodes/ClusterGroupNode'
import ModuleSummaryNode from './nodes/ModuleSummaryNode'
import ModuleGhostNode from './nodes/ModuleGhostNode'
import ZoneMoreNode from './nodes/ZoneMoreNode'
import TextNode from './nodes/TextNode'

export const NODE_TYPES = {
  custom: CustomNode,
  moduleGroup: ModuleGroupNode,
  zoneGroup: ZoneGroupNode,
  clusterGroup: ClusterGroupNode,
  moduleSummary: ModuleSummaryNode,
  moduleGhost: ModuleGhostNode,
  zoneMore: ZoneMoreNode,
  text: TextNode,
}
