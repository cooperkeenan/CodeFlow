from shared.flow_endpoints.endpoint_group import EndpointGroup
from shared.models.flow_graph import FlowNode

_PREVIEW_PATHS = 3


class GroupMeta:
    def of(self, group: EndpointGroup) -> dict:
        return {
            "id": group.id,
            "name": group.name,
            "parent_id": group.parent_id,
            "entry_id": group.entry_id,
            "route_count": group.route_count,
            "is_leaf": group.is_leaf,
            "overflow": group.overflow,
        }

    def title(self, group: EndpointGroup) -> str:
        noun = "route" if group.route_count == 1 else "routes"
        return f"{group.name} · {group.route_count} {noun}"

    def root_fields(self, group: EndpointGroup, node: FlowNode) -> dict:
        title = self.title(group)
        return {
            "label": title,
            "llm_label": title,
            "folded_count": group.route_count,
            "one_liner": node.one_liner if group.id == group.entry_id else self.preview(group),
        }

    def preview(self, group: EndpointGroup) -> str:
        return ", ".join(sorted({route.path for route in group.routes})[:_PREVIEW_PATHS])
