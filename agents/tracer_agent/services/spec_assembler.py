import logging

from shared.models.diagram_spec import (
    Component,
    ComponentIO,
    DiagramSpec,
    Edge,
    ExternalActor,
    Module,
)
from shared.models.repo_blueprint import RepoBlueprint

logger = logging.getLogger(__name__)

_EDGE_TYPES = {"http", "import", "database", "event", "call"}
_ACTOR_TYPES = {"database", "api", "webhook", "browser"}


class SpecAssembler:
    def assemble(self, blueprint: RepoBlueprint, raw: dict, architecture_type: str) -> DiagramSpec:
        index = self._dir_index(blueprint)
        modules = {
            m.root_path: Module(
                name=m.name, description=m.description, root_path=m.root_path, zones={}
            )
            for m in blueprint.modules
        }
        for component in self._components(raw):
            placement = self._place(component.file_path, index)
            if placement is None:
                logger.warning("Dropping unplaceable component %s (%s)", component.name, component.file_path)
                continue
            root, zone = placement
            modules[root].zones.setdefault(zone, []).append(component)
        return DiagramSpec(
            architecture_type=architecture_type,
            modules=list(modules.values()),
            edges=self._edges(raw),
            external_actors=self._actors(raw),
            entry_points=[e for e in raw.get("entry_points", []) if isinstance(e, str)],
        )

    def _dir_index(self, blueprint: RepoBlueprint) -> list[tuple[str, str, str]]:
        index = [
            (directory, module.root_path, zone.name)
            for module in blueprint.modules
            for zone in module.zones
            for directory in zone.directories
        ]
        index.sort(key=lambda t: len(t[0]), reverse=True)
        return index

    def _place(self, file_path: str, index: list[tuple[str, str, str]]) -> tuple[str, str] | None:
        for directory, root, zone in index:
            if file_path.startswith(directory):
                return root, zone
        return None

    def _components(self, raw: dict) -> list[Component]:
        components = []
        for c in raw.get("components", []):
            if not isinstance(c, dict) or not c.get("name") or not c.get("file_path"):
                continue
            io = c.get("io")
            io_model = None
            if isinstance(io, dict):
                io_model = ComponentIO(
                    inputs=[v for v in io.get("inputs", []) if v],
                    outputs=[v for v in io.get("outputs", []) if v],
                )
            components.append(Component(
                name=c["name"],
                description=str(c.get("description", "")),
                file_path=c["file_path"],
                io=io_model,
                children=[ch for ch in c.get("children", []) if isinstance(ch, str)],
            ))
        return components

    def _edges(self, raw: dict) -> list[Edge]:
        edges = []
        for e in raw.get("edges", []):
            if not isinstance(e, dict):
                continue
            source, target, edge_type = e.get("source"), e.get("target"), e.get("edge_type")
            if source and target and edge_type in _EDGE_TYPES:
                edges.append(Edge(source=source, target=target, edge_type=edge_type))
        return edges

    def _actors(self, raw: dict) -> list[ExternalActor]:
        actors = []
        for a in raw.get("external_actors", []):
            if isinstance(a, dict) and a.get("name") and a.get("type") in _ACTOR_TYPES:
                actors.append(ExternalActor(
                    name=a["name"], type=a["type"], description=str(a.get("description", ""))
                ))
        return actors
