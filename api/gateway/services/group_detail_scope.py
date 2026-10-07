from gateway.services.group_summaries import GroupSummaries

from shared.flow_endpoints.endpoint_group import EndpointGroup, GroupForest
from shared.models.endpoint_contract import EndpointDetail
from shared.models.flow_graph import RouteMember


class GroupDetailScope:
    def __init__(self, summaries: GroupSummaries) -> None:
        self._summaries = summaries

    def routes(self, members: list[RouteMember], group: EndpointGroup) -> list[RouteMember]:
        wanted = {(r.handler_fqn, r.method, r.path) for r in group.routes}
        return [m for m in members if (m.handler_fqn, m.method, m.path) in wanted]

    def apply(self, detail: EndpointDetail, forest: GroupForest, group: EndpointGroup) -> EndpointDetail:
        return detail.model_copy(
            update={
                "id": group.id,
                "title": group.name,
                "group": self._summaries.of(forest, group),
                "children": self._summaries.children(forest, group),
            }
        )
