from dataclasses import dataclass


@dataclass(frozen=True)
class GroupRoute:
    handler_fqn: str
    method: str
    path: str


@dataclass(frozen=True)
class EndpointGroup:
    id: str
    name: str
    parent_id: str | None
    entry_id: str
    routes: tuple[GroupRoute, ...]
    children: tuple[str, ...]
    overflow: bool

    @property
    def is_leaf(self) -> bool:
        return not self.children

    @property
    def route_count(self) -> int:
        return len(self.routes)


@dataclass(frozen=True)
class GroupForest:
    groups: tuple[EndpointGroup, ...]

    def find(self, group_id: str) -> EndpointGroup | None:
        return next((g for g in self.groups if g.id == group_id), None)

    def children(self, group_id: str) -> list[EndpointGroup]:
        parent = self.find(group_id)
        if parent is None:
            return []
        return [g for g in (self.find(c) for c in parent.children) if g is not None]

    def leaves(self) -> list[EndpointGroup]:
        return [g for g in self.groups if g.is_leaf]

    def preorder(self) -> list[EndpointGroup]:
        return list(self.groups)

    def leaf_of(
        self, entry_id: str, handler_fqn: str, method: str, path: str
    ) -> EndpointGroup | None:
        wanted = GroupRoute(handler_fqn, method, path)
        return next(
            (g for g in self.leaves() if g.entry_id == entry_id and wanted in g.routes), None
        )
