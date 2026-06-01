import logging
from collections.abc import Iterator
from dataclasses import dataclass

from shared.models.diagram_spec import Component, DiagramSpec, Module

logger = logging.getLogger(__name__)


def _names(spec: DiagramSpec) -> set[str]:
    return {c.name for m in spec.modules for comps in m.zones.values() for c in comps}


def _iter(spec: DiagramSpec) -> Iterator[tuple[str, Component]]:
    for module in spec.modules:
        for zone, comps in module.zones.items():
            for component in comps:
                yield zone, component


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    correctable_warnings: list[str]
    fixed_spec: DiagramSpec


class GraphValidator:
    def validate(self, spec: DiagramSpec, evidence: dict) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        correctable: list[str] = []
        fixed = self._apply_hard_rules(spec, errors)
        self._apply_warning_rules(fixed, evidence, warnings, correctable)
        return ValidationResult(
            is_valid=not (errors or warnings or correctable),
            errors=errors,
            warnings=warnings,
            correctable_warnings=correctable,
            fixed_spec=fixed,
        )

    def _apply_hard_rules(self, spec: DiagramSpec, errors: list[str]) -> DiagramSpec:
        names = _names(spec)
        edges = self._clean_edges(spec.edges, names, errors)
        entry_points = []
        for ep in spec.entry_points:
            if ep in names:
                entry_points.append(ep)
            else:
                errors.append(f"R2: Removed entry_point {ep} (not in layers)")
        modules = [self._fix_module(m, names, errors) for m in spec.modules]
        return spec.model_copy(update={"edges": edges, "entry_points": entry_points, "modules": modules})

    def _clean_edges(self, raw_edges: list, names: set[str], errors: list[str]) -> list:
        seen: set[tuple] = set()
        out = []
        for e in raw_edges:
            if e.source not in names or e.target not in names:
                errors.append(f"R1: Removed edge {e.source} -> {e.target} (unknown component)")
            elif e.source == e.target:
                errors.append(f"R5: Removed self-edge {e.source}")
            elif (key := (e.source, e.target, e.edge_type)) in seen:
                errors.append(f"R4: Removed duplicate edge {e.source} -> {e.target}")
            else:
                seen.add(key)
                out.append(e)
        return out

    def _fix_module(self, module: Module, names: set[str], errors: list[str]) -> Module:
        zones = {}
        for zone, comps in module.zones.items():
            zones[zone] = [self._fix_component(c, names, errors) for c in comps]
        return module.model_copy(update={"zones": zones})

    def _fix_component(self, c: Component, names: set[str], errors: list[str]) -> Component:
        children = []
        for child in c.children:
            if child in names:
                children.append(child)
            else:
                errors.append(f"R3: Removed child {child} from {c.name} (unknown component)")
        io = c.io
        if io is not None:
            inputs = [v for v in io.inputs if v != ""]
            outputs = [v for v in io.outputs if v != ""]
            if len(inputs) != len(io.inputs) or len(outputs) != len(io.outputs):
                errors.append(f"R6: stripped empty io entry from {c.name}")
            io = io.model_copy(update={"inputs": inputs, "outputs": outputs})
        return c.model_copy(update={"children": children, "io": io})

    def _apply_warning_rules(
        self, spec: DiagramSpec, evidence: dict, warnings: list[str], correctable: list[str]
    ) -> None:
        names = _names(spec)
        edge_pairs = {(e.source, e.target) for e in spec.edges}
        sigs = evidence.get("signatures", {})

        for zone, c in _iter(spec):
            if any(c.name in (e.source, e.target) for e in spec.edges):
                continue
            if zone == "data" and not self._has_component_param(sigs.get(c.name, {}), names):
                continue
            correctable.append(f"W1: {c.name} has no incoming or outgoing edges")

        for ce in evidence.get("confirmed_edges", []):
            if (ce["from"], ce["to"]) not in edge_pairs:
                correctable.append(f"W2: confirmed_edge {ce['from']} -> {ce['to']} missing from spec")

        evidence_pairs = {(e["from"], e["to"]) for e in evidence.get("import_edges", [])} | {
            (e["from"], e["to"]) for e in evidence.get("call_edges", [])
        }
        for e in spec.edges:
            if (e.source, e.target) not in evidence_pairs:
                warnings.append(f"W3: Edge {e.source} -> {e.target} not in evidence")

        for _, c in _iter(spec):
            sig = sigs.get(c.name, {})
            has_params = any(m.get("params") for m in sig.get("public_methods", []))
            io_empty = c.io is None or (not c.io.inputs and not c.io.outputs)
            if has_params and io_empty:
                warnings.append(f"W4: {c.name} has empty io but public methods with parameters")
            for child in c.children:
                if (c.name, child) not in edge_pairs:
                    correctable.append(f"W5: {c.name} lists {child} as child but no edge {c.name} -> {child} exists")

    def _has_component_param(self, sig: dict, names: set[str]) -> bool:
        return any(
            p.get("annotation") in names
            for m in sig.get("public_methods", [])
            for p in m.get("params", [])
        )
