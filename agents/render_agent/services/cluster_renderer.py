from services.mermaid_ids import node_id

from shared.models.diagram_spec import Cluster, Component, Module


class ClusterRenderer:
    def render_zone(
        self,
        module: str,
        zone: str,
        components: list[Component],
        entry_points: set[str],
        clusters: list[Cluster],
    ) -> list[str]:
        zone_id = f"{node_id(module)}__{node_id(zone)}"
        by_name = {c.name: c for c in components}
        placed: set[str] = set()
        lines = [f'        subgraph {zone_id}["{zone}"]']
        for index, cluster in enumerate(clusters):
            lines += self._cluster(zone_id, cluster, by_name, entry_points, placed, index)
        for component in components:
            if component.nested or component.name in placed:
                continue
            placed.add(component.name)
            lines.append(self._node(component, entry_points))
        lines.append("        end")
        return lines

    def _cluster(
        self,
        prefix: str,
        cluster: Cluster,
        by_name: dict[str, Component],
        entry_points: set[str],
        placed: set[str],
        index: int,
    ) -> list[str]:
        cluster_id = f"{prefix}__c{index}"
        lines = [f'            subgraph {cluster_id}["{cluster.label}"]']
        for name in cluster.members:
            component = by_name.get(name)
            if component and name not in placed:
                placed.add(name)
                lines.append(self._node(component, entry_points))
        for child_index, child in enumerate(cluster.children):
            lines += self._cluster(cluster_id, child, by_name, entry_points, placed, child_index)
        lines.append("            end")
        return lines

    def _node(self, component: Component, entry_points: set[str]) -> str:
        shape = f'(("{component.name}"))' if component.name in entry_points else f'["{component.name}"]'
        return f"            {node_id(component.name)}{shape}"


def order_pairs(module: Module) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for plan in module.cluster_plan:
        for cluster in plan.clusters:
            _collect(cluster, pairs)
    return pairs


def _collect(cluster: Cluster, pairs: list[tuple[str, str]]) -> None:
    members = cluster.members
    if cluster.style == "pipeline":
        pairs += [(members[i], members[i + 1]) for i in range(len(members) - 1)]
    elif cluster.style in ("hierarchy", "hub") and members:
        pairs += [(members[0], member) for member in members[1:]]
    for child in cluster.children:
        _collect(child, pairs)
