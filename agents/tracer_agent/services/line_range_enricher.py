from shared.models.diagram_spec import DiagramSpec


class LineRangeEnricher:
    def enrich(self, spec: DiagramSpec, signatures: dict) -> DiagramSpec:
        for module in spec.modules:
            for components in module.zones.values():
                for component in components:
                    entry = signatures.get(component.name)
                    if entry and entry.get("file_path") == component.file_path:
                        component.start_line = entry.get("start_line")
                        component.end_line = entry.get("end_line")
        return spec
