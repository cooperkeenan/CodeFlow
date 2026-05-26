import logging
from dataclasses import dataclass

from shared.models.diagram_spec import DiagramSpec

logger = logging.getLogger(__name__)


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
        correctable_warnings: list[str] = []
        fixed_spec = self._apply_hard_rules(spec, errors)
        self._apply_warning_rules(fixed_spec, evidence, warnings, correctable_warnings)
        return ValidationResult(
            is_valid=not errors and not warnings and not correctable_warnings,
            errors=errors,
            warnings=warnings,
            correctable_warnings=correctable_warnings,
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
            fixed = []
            for c in components:
                valid_children = []
                for child in c.children:
                    if child not in all_components:
                        errors.append(f"R3: Removed child {child} from {c.name} (unknown component)")
                    else:
                        valid_children.append(child)
                fixed.append(c.model_copy(update={"children": valid_children}))
            fixed_layers[layer_name] = fixed

        for layer_name, components in fixed_layers.items():
            cleaned = []
            for c in components:
                if c.io is None:
                    cleaned.append(c)
                    continue
                inputs = [v for v in c.io.inputs if v != ""]
                outputs = [v for v in c.io.outputs if v != ""]
                for _ in range(len(c.io.inputs) - len(inputs)):
                    errors.append(f"R6: stripped empty io entry from {c.name}")
                for _ in range(len(c.io.outputs) - len(outputs)):
                    errors.append(f"R6: stripped empty io entry from {c.name}")
                cleaned.append(c.model_copy(update={"io": c.io.model_copy(update={"inputs": inputs, "outputs": outputs})}))
            fixed_layers[layer_name] = cleaned

        return spec.model_copy(update={
            "edges": final_edges,
            "entry_points": valid_eps,
            "layers": fixed_layers,
        })

    def _apply_warning_rules(
        self, spec: DiagramSpec, evidence: dict, warnings: list[str], correctable_warnings: list[str]
    ) -> None:
        all_components = {c.name for layer in spec.layers.values() for c in layer}
        edge_pairs = {(e.source, e.target) for e in spec.edges}
        signatures = evidence.get("signatures", {})

        for layer_name, components in spec.layers.items():
            for c in components:
                if any(c.name in (e.source, e.target) for e in spec.edges):
                    continue
                if layer_name == "data":
                    methods = signatures.get(c.name, {}).get("public_methods", [])
                    has_component_param = any(
                        p.get("annotation") in all_components
                        for m in methods
                        for p in m.get("params", [])
                    )
                    if not has_component_param:
                        continue
                correctable_warnings.append(f"W1: {c.name} has no incoming or outgoing edges")

        for ce in evidence.get("confirmed_edges", []):
            if (ce["from"], ce["to"]) not in edge_pairs:
                correctable_warnings.append(f"W2: confirmed_edge {ce['from']} -> {ce['to']} missing from spec")

        import_pairs = {(e["from"], e["to"]) for e in evidence.get("import_edges", [])}
        call_pairs = {(e["from"], e["to"]) for e in evidence.get("call_edges", [])}
        evidence_pairs = import_pairs | call_pairs
        for e in spec.edges:
            if (e.source, e.target) not in evidence_pairs:
                warnings.append(f"W3: Edge {e.source} -> {e.target} not in evidence")

        for layer in spec.layers.values():
            for c in layer:
                sig = signatures.get(c.name, {})
                has_params = any(m.get("params") for m in sig.get("public_methods", []))
                io_empty = c.io is None or (not c.io.inputs and not c.io.outputs)
                if has_params and io_empty:
                    warnings.append(f"W4: {c.name} has empty io but public methods with parameters")

        for layer in spec.layers.values():
            for c in layer:
                for child in c.children:
                    if (c.name, child) not in edge_pairs:
                        correctable_warnings.append(f"W5: {c.name} lists {child} as child but no edge {c.name} -> {child} exists")
