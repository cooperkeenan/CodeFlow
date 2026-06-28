from dataclasses import dataclass, field

from shared.models.diagram_spec import ComponentTier, DiagramSpec

VALID_TIERS = {"primary", "secondary"}


@dataclass
class SemanticAnnotations:
    module_purposes: dict[str, str] = field(default_factory=dict)
    component_roles: dict[str, str] = field(default_factory=dict)
    component_tiers: dict[str, ComponentTier] = field(default_factory=dict)
    primary_edges: set[tuple[str, str]] = field(default_factory=set)


class SemanticValidator:
    def validate(
        self,
        raw: dict,
        spec: DiagramSpec,
        fallback_tiers: dict[str, ComponentTier],
    ) -> SemanticAnnotations:
        valid_components = self._component_names(spec)
        valid_modules = {m.name for m in spec.modules}
        tiers: dict[str, ComponentTier] = dict(fallback_tiers)
        roles: dict[str, str] = {}
        for entry in raw.get("components", []) or []:
            self._apply_component(entry, valid_components, tiers, roles)
        purposes = self._purposes(raw.get("modules", []) or [], valid_modules)
        edges = self._primary_edges(raw.get("primary_edges", []) or [], valid_components, tiers)
        return SemanticAnnotations(purposes, roles, tiers, edges)

    def _component_names(self, spec: DiagramSpec) -> set[str]:
        return {
            component.name
            for module in spec.modules
            for components in module.zones.values()
            for component in components
        }

    def _apply_component(
        self,
        entry: dict,
        valid: set[str],
        tiers: dict[str, ComponentTier],
        roles: dict[str, str],
    ) -> None:
        if not isinstance(entry, dict):
            return
        name = entry.get("name")
        if name not in valid:
            return
        tier = entry.get("tier")
        if tier in VALID_TIERS:
            tiers[name] = tier
        role = entry.get("role")
        if isinstance(role, str) and role:
            roles[name] = role

    def _purposes(self, entries: list, valid_modules: set[str]) -> dict[str, str]:
        purposes: dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            purpose = entry.get("purpose")
            if name in valid_modules and isinstance(purpose, str) and purpose:
                purposes[name] = purpose
        return purposes

    def _primary_edges(
        self, entries: list, valid: set[str], tiers: dict[str, ComponentTier]
    ) -> set[tuple[str, str]]:
        edges: set[tuple[str, str]] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            source = entry.get("source")
            target = entry.get("target")
            if source not in valid or target not in valid:
                continue
            if tiers.get(source) == "primary" and tiers.get(target) == "primary":
                edges.add((source, target))
        return edges
