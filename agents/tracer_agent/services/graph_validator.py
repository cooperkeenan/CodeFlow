import logging
from dataclasses import dataclass

from shared.models.diagram_spec import DiagramSpec

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    fixed_spec: DiagramSpec


class GraphValidator:
    def validate(self, spec: DiagramSpec, evidence: dict) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        fixed_spec = self._apply_hard_rules(spec, errors)
        self._apply_warning_rules(fixed_spec, evidence, warnings)
        return ValidationResult(
            is_valid=not errors and not warnings,
            errors=errors,
            warnings=warnings,
            fixed_spec=fixed_spec,
        )

    def _apply_hard_rules(self, spec: DiagramSpec, errors: list[str]) -> DiagramSpec:
        all_components = {c.name for layer in spec.layers.values() for c in layer}

        valid_edges = []
        for e in spec.edges:
            if e.source not in all_components or e.target not in all_components:
                errors.append(f"R1: Removed edge {e.source} -> {e.target} (unknown component)")
            else:
                valid_edges.append(e)

        seen: set[tuple] = set()
        deduped = []
        for e in valid_edges:
            key = (e.source, e.target, e.edge_type)
            if key in seen:
                errors.append(f"R4: Removed duplicate edge {e.source} -> {e.target}")
            else:
                seen.add(key)
                deduped.append(e)

        final_edges = []
        for e in deduped:
            if e.source == e.target:
                errors.append(f"R5: Removed self-edge {e.source}")
            else:
                final_edges.append(e)

        valid_eps = []
        for ep in spec.entry_points:
            if ep not in all_components:
                errors.append(f"R2: Removed entry_point {ep} (not in layers)")
            else:
                valid_eps.append(ep)

        fixed_layers = {}
        for layer_name, components in spec.layers.items():
            layer_names = {c.name for c in components}
            fixed = []
            for c in components:
                valid_children = []
                for child in c.children:
                    if child not in layer_names:
                        errors.append(f"R3: Removed child {child} from {c.name} (not in same layer)")
                    else:
                        valid_children.append(child)
                fixed.append(c.model_copy(update={"children": valid_children}))
            fixed_layers[layer_name] = fixed

        return spec.model_copy(update={
            "edges": final_edges,
            "entry_points": valid_eps,
            "layers": fixed_layers,
        })

    def _apply_warning_rules(self, spec: DiagramSpec, evidence: dict, warnings: list[str]) -> None:
        all_components = {c.name for layer in spec.layers.values() for c in layer}
        edge_pairs = {(e.source, e.target) for e in spec.edges}

        for name in all_components:
            if not any(name in (e.source, e.target) for e in spec.edges):
                warnings.append(f"W1: {name} has no incoming or outgoing edges")

        for ce in evidence.get("confirmed_edges", []):
            if (ce["from"], ce["to"]) not in edge_pairs:
                warnings.append(f"W2: confirmed_edge {ce['from']} -> {ce['to']} missing from spec")

        import_pairs = {(e["from"], e["to"]) for e in evidence.get("import_edges", [])}
        call_pairs = {(e["from"], e["to"]) for e in evidence.get("call_edges", [])}
        evidence_pairs = import_pairs | call_pairs
        for e in spec.edges:
            if (e.source, e.target) not in evidence_pairs:
                warnings.append(f"W3: Edge {e.source} -> {e.target} not in evidence")

        signatures = evidence.get("signatures", {})
        for layer in spec.layers.values():
            for c in layer:
                sig = signatures.get(c.name, {})
                has_params = any(m.get("params") for m in sig.get("public_methods", []))
                io_empty = c.io is None or (not c.io.inputs and not c.io.outputs)
                if has_params and io_empty:
                    warnings.append(f"W4: {c.name} has empty io but public methods with parameters")
