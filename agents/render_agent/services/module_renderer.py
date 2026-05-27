from services.mermaid_ids import node_id

from shared.models.diagram_spec import DiagramSpec, ExternalActor

_ACTOR_SHAPES: dict[str, tuple[str, str]] = {
    "database": ("[(", ")]"),
    "api":      ("([", "])"),
    "webhook":  ("([", "])"),
    "browser":  ("([", "])"),
}


class ModuleRenderer:
    def render_actors(self, actors: list[ExternalActor]) -> list[str]:
        if not actors:
            return []
        lines = ["    subgraph External[External Systems]"]
        for actor in actors:
            open_b, close_b = _ACTOR_SHAPES.get(actor.type, ("([", "])"))
            lines.append(f'        {node_id(actor.name)}{open_b}"{actor.name}"{close_b}')
        lines.append("    end")
        return lines

    def render(self, spec: DiagramSpec) -> list[str]:
        entry_points = set(spec.entry_points)
        lines = []
        for module in spec.modules:
            if not any(module.zones.values()):
                continue
            lines.append(f'    subgraph mod_{node_id(module.name)}["{module.name}"]')
            for zone, components in module.zones.items():
                if not components:
                    continue
                lines += self._zone(module.name, zone, components, entry_points)
            lines.append("    end")
        return lines

    def _zone(self, module: str, zone: str, components, entry_points: set[str]) -> list[str]:
        zone_id = f"{node_id(module)}__{node_id(zone)}"
        lines = [f'        subgraph {zone_id}["{zone}"]']
        for c in components:
            shape = f'(("{c.name}"))' if c.name in entry_points else f'["{c.name}"]'
            lines.append(f'            {node_id(c.name)}{shape}')
        lines.append("        end")
        return lines
