from typing import cast

from shared.models.diagram_spec import Cluster, LayoutStyle, Module, ZoneClusterPlan

VALID_STYLES: frozenset[str] = frozenset(
    {"grid", "stack", "pipeline", "hierarchy", "hub"}
)
MAX_HIERARCHY_CHILDREN = 6
MAX_HUB_SPOKES = 8


class ClusterValidator:
    def validate(self, raw: dict, module: Module) -> list[ZoneClusterPlan]:
        plans: list[ZoneClusterPlan] = []
        for entry in raw.get("zones", []) or []:
            plan = self._zone_plan(entry, module)
            if plan and plan.clusters:
                plans.append(plan)
        return plans

    def _zone_plan(self, entry: dict, module: Module) -> ZoneClusterPlan | None:
        if not isinstance(entry, dict):
            return None
        zone = entry.get("zone")
        if not isinstance(zone, str):
            return None
        valid = {c.name for c in module.zones.get(zone, [])}
        if not valid:
            return None
        used: set[str] = set()
        clusters = [
            cluster
            for raw_cluster in entry.get("clusters", []) or []
            if (cluster := self._cluster(raw_cluster, valid, used, depth=0))
        ]
        return ZoneClusterPlan(zone=zone, clusters=clusters)

    def _cluster(
        self, raw: dict, valid: set[str], used: set[str], depth: int
    ) -> Cluster | None:
        if not isinstance(raw, dict):
            return None
        members = self._members(raw.get("members", []), valid, used)
        children = self._children(raw.get("children", []), valid, used, depth)
        if not members and not children:
            return None
        label = raw.get("label") or "Group"
        style = self._style(raw.get("style"), members)
        return Cluster(label=str(label), style=style, members=members, children=children)

    def _members(self, raw: list, valid: set[str], used: set[str]) -> list[str]:
        members: list[str] = []
        for name in raw or []:
            if name in valid and name not in used:
                used.add(name)
                members.append(name)
        return members

    def _children(
        self, raw: list, valid: set[str], used: set[str], depth: int
    ) -> list[Cluster]:
        if depth >= 1:
            return []
        children: list[Cluster] = []
        for raw_child in raw or []:
            child = self._cluster(raw_child, valid, used, depth + 1)
            if child:
                children.append(child)
        return children

    def _style(self, raw_style: object, members: list[str]) -> LayoutStyle:
        style = raw_style if raw_style in VALID_STYLES else "grid"
        spokes = len(members) - 1
        if style == "hierarchy" and spokes > MAX_HIERARCHY_CHILDREN:
            return "grid"
        if style == "hub" and spokes > MAX_HUB_SPOKES:
            return "grid"
        if style in ("pipeline", "stack", "hierarchy", "hub") and len(members) < 2:
            return "grid"
        return cast(LayoutStyle, style)
