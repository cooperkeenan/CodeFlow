from services.cluster_renderer import order_pairs
from services.mermaid_ids import node_id

from shared.models.diagram_spec import DiagramSpec

_EDGE_STYLES: dict[str, str] = {
    "call":     "-->",
    "import":   "-.->",
    "database": "-->",
    "http":     "-->",
    "event":    "-. event .->",
}

_LABELLED = ("http", "event", "database")


class EdgeRenderer:
    def render(self, spec: DiagramSpec) -> list[str]:
        internal = self._internal_ids(spec)
        actor_ids = {node_id(a.name) for a in spec.external_actors}
        lines = []
        for edge in spec.edges:
            source, target = node_id(edge.source), node_id(edge.target)
            if source not in internal or target in actor_ids:
                continue
            arrow = _EDGE_STYLES.get(edge.edge_type, "-->")
            label = f"|{edge.edge_type}|" if edge.edge_type in _LABELLED else ""
            lines.append(f"    {source} {arrow}{label} {target}")
        lines += self._order_edges(spec, internal)
        lines += self._actor_edges(spec, internal)
        return lines

    def _order_edges(self, spec: DiagramSpec, internal: set[str]) -> list[str]:
        seen = {(node_id(e.source), node_id(e.target)) for e in spec.edges}
        lines = []
        for module in spec.modules:
            for source, target in order_pairs(module):
                source_id, target_id = node_id(source), node_id(target)
                if source_id not in internal or target_id not in internal:
                    continue
                if (source_id, target_id) in seen:
                    continue
                seen.add((source_id, target_id))
                lines.append(f"    {source_id} --> {target_id}")
        return lines

    def _internal_ids(self, spec: DiagramSpec) -> set[str]:
        return {
            node_id(c.name)
            for m in spec.modules
            for comps in m.zones.values()
            for c in comps
        }

    def _actor_edges(self, spec: DiagramSpec, internal: set[str]) -> list[str]:
        lines = []
        entry_ids = {node_id(ep) for ep in spec.entry_points if node_id(ep) in internal}
        for actor in spec.external_actors:
            actor_id = node_id(actor.name)
            if actor.type == "database":
                sources = {
                    node_id(e.source) for e in spec.edges
                    if e.edge_type == "database" and node_id(e.source) in internal
                }
                lines += [f"    {src} -->|database| {actor_id}" for src in sorted(sources)]
            elif actor.type == "webhook":
                lines += [f"    {src} -->|webhook| {actor_id}" for src in sorted(entry_ids)]
            else:
                lines += [f"    {src} -->|http| {actor_id}" for src in sorted(entry_ids)]
        return lines
