import logging

from shared.models.diagram_spec import Component, DiagramSpec, ExternalActor

logger = logging.getLogger(__name__)

_EDGE_STYLES: dict[str, str] = {
    "call":     "-->",
    "import":   "-.->",
    "database": "-->",
    "http":     "-->",
    "event":    "-. event .->",
}

_ACTOR_SHAPES: dict[str, tuple[str, str]] = {
    "database": ("[(", ")]"),
    "api":      ("([", "])"),
    "webhook":  ("([", "])"),
    "browser":  ("([", "])"),
}


class MermaidService:
    def render(self, spec: DiagramSpec) -> str:
        logger.info("Rendering %s diagram", spec.architecture_type)
        lines = ["flowchart TD"]
        lines += self._external_actors(spec.external_actors)
        lines += self._layers(spec)
        lines += self._edges(spec)
        diagram = "\n".join(lines)
        logger.info("Diagram complete: %d lines", len(lines))
        return diagram

    # ── Subgraphs ─────────────────────────────────────────────────────────────

    def _external_actors(self, actors: list[ExternalActor]) -> list[str]:
        if not actors:
            return []
        lines = ["    subgraph External[External Systems]"]
        for actor in actors:
            open_b, close_b = _ACTOR_SHAPES.get(actor.type, ("([", "])"))
            lines.append(f'        {self._id(actor.name)}{open_b}"{actor.name}"{close_b}')
        lines.append("    end")
        return lines

    def _layers(self, spec: DiagramSpec) -> list[str]:
        lines = []
        all_component_names = {c.name for layer in spec.layers.values() for c in layer}

        for layer_name, components in spec.layers.items():
            top_level = [
                c for c in components
                if c.name not in self._same_layer_children(layer_name, spec)
            ]
            if not top_level:
                continue
            lines.append(f'    subgraph {self._id(layer_name)}["{layer_name.capitalize()} Layer"]')
            for component in top_level:
                lines += self._component_block(
                    component, layer_name, spec, all_component_names, indent=8
                )
            lines.append("    end")
        return lines

    def _component_block(
        self,
        component: Component,
        layer_name: str,
        spec: DiagramSpec,
        all_component_names: set[str],
        indent: int,
    ) -> list[str]:
        pad = " " * indent
        node_id = self._id(component.name)
        is_entry = component.name in spec.entry_points
        shape = f'(("{component.name}"))' if is_entry else f'["{component.name}"]'

        same_layer_names = {c.name for c in spec.layers.get(layer_name, [])}
        nested = [n for n in component.children if n in same_layer_names]
        orphaned = [n for n in component.children if n not in all_component_names]

        if nested or orphaned:
            inner_id = f"{node_id}_node"
            lines = [f'{pad}subgraph {node_id}_grp["{component.name}"]']
            lines.append(f'{pad}    {inner_id}["{component.name}"]')
            for child_name in nested:
                child = self._find_component(child_name, spec)
                if child:
                    lines += self._component_block(
                        child, layer_name, spec, all_component_names, indent + 4
                    )
                else:
                    lines.append(f'{pad}    {self._id(child_name)}["{child_name}"]')
            for child_name in orphaned:
                lines.append(f'{pad}    {self._id(child_name)}["{child_name}"]')
            lines.append(f"{pad}end")
            return lines

        return [f"{pad}{node_id}{shape}"]

    # ── Edges ─────────────────────────────────────────────────────────────────

    def _edges(self, spec: DiagramSpec) -> list[str]:
        actor_ids = {self._id(a.name) for a in spec.external_actors}
        internal_ids = self._all_internal_ids(spec)
        lines = []

        for edge in spec.edges:
            source = self._resolve_id(edge.source, spec)
            target = self._resolve_id(edge.target, spec)
            if target in actor_ids or source not in internal_ids:
                continue
            arrow = _EDGE_STYLES.get(edge.edge_type, "-->")
            label = f"|{edge.edge_type}|" if edge.edge_type in ("http", "event", "database") else ""
            lines.append(f"    {source} {arrow}{label} {target}")

        lines += self._external_actor_edges(spec, internal_ids)
        return lines

    def _external_actor_edges(
        self,
        spec: DiagramSpec,
        internal_ids: set[str],
    ) -> list[str]:
        lines = []
        all_components = [c for layer in spec.layers.values() for c in layer]

        for actor in spec.external_actors:
            actor_id = self._id(actor.name)

            if actor.type == "database":
                sources = {
                    self._resolve_id(e.source, spec)
                    for e in spec.edges
                    if e.edge_type == "database"
                    and self._id(e.source) in internal_ids
                }
                for src in sources:
                    lines.append(f"    {src} -->|database| {actor_id}")

            elif actor.type in ("api", "browser"):
                sources = {
                    self._resolve_id(c.name, spec)
                    for c in all_components
                    if any(kw in c.name.lower() for kw in ("scraper", "facebook"))
                }
                for src in sources:
                    lines.append(f"    {src} -->|http| {actor_id}")

            elif actor.type == "webhook":
                sources = {self._resolve_id(e, spec) for e in spec.entry_points}
                for src in sources:
                    lines.append(f"    {src} -->|webhook| {actor_id}")

        return lines

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _same_layer_children(self, layer_name: str, spec: DiagramSpec) -> set[str]:
        layer_names = {c.name for c in spec.layers.get(layer_name, [])}
        return {
            child
            for component in spec.layers.get(layer_name, [])
            for child in component.children
            if child in layer_names
        }

    def _all_internal_ids(self, spec: DiagramSpec) -> set[str]:
        ids: set[str] = set()
        all_component_names = {c.name for layer in spec.layers.values() for c in layer}
        for layer_name, components in spec.layers.items():
            same_layer_names = {c.name for c in components}
            for component in components:
                node_id = self._id(component.name)
                nested = [n for n in component.children if n in same_layer_names]
                orphaned = [n for n in component.children if n not in all_component_names]
                if nested or orphaned:
                    ids.add(f"{node_id}_node")
                else:
                    ids.add(node_id)
                for child in component.children:
                    ids.add(self._id(child))
        return ids

    def _resolve_id(self, name: str, spec: DiagramSpec) -> str:
        all_component_names = {c.name for layer in spec.layers.values() for c in layer}
        node_id = self._id(name)
        for layer_name, components in spec.layers.items():
            same_layer_names = {c.name for c in components}
            for component in components:
                if component.name != name:
                    continue
                nested = [n for n in component.children if n in same_layer_names]
                orphaned = [n for n in component.children if n not in all_component_names]
                if nested or orphaned:
                    return f"{node_id}_node"
        return node_id

    def _find_component(self, name: str, spec: DiagramSpec) -> Component | None:
        for components in spec.layers.values():
            for component in components:
                if component.name == name:
                    return component
        return None

    def _id(self, name: str) -> str:
        return (
            name.replace(" ", "_")
                .replace("-", "_")
                .replace("/", "_")
                .replace(".", "_")
        )