from shared.flow_endpoints.endpoint_group import EndpointGroup, GroupForest
from shared.models.endpoint_group_summary import EndpointGroupSummary


class GroupSummaries:
    def all(self, forest: GroupForest) -> list[EndpointGroupSummary]:
        return [self.of(forest, group) for group in forest.preorder()]

    def of(self, forest: GroupForest, group: EndpointGroup) -> EndpointGroupSummary:
        return EndpointGroupSummary(
            id=group.id,
            parent_id=group.parent_id,
            name=group.name,
            route_count=group.route_count,
            is_leaf=group.is_leaf,
            depth=self._depth(forest, group),
        )

    def children(self, forest: GroupForest, group: EndpointGroup) -> list[EndpointGroupSummary]:
        return [self.of(forest, child) for child in forest.children(group.id)]

    def _depth(self, forest: GroupForest, group: EndpointGroup) -> int:
        depth = 0
        current = group
        while current.parent_id is not None:
            parent = forest.find(current.parent_id)
            if parent is None:
                break
            depth += 1
            current = parent
        return depth
