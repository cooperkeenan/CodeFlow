from shared.flow_endpoints.endpoint_group import EndpointGroup


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
