from shared.models.diagram_spec import DiagramSpec, Edge


class EdgeRecovery:
    def recover(self, spec: DiagramSpec, evidence: dict) -> DiagramSpec:
        names = {c.name for m in spec.modules for cs in m.zones.values() for c in cs}
        existing = {(e.source, e.target) for e in spec.edges}
        recovered: list[Edge] = []
        for ce in evidence.get("confirmed_edges", []):
            src, tgt = ce.get("from"), ce.get("to")
            if src in names and tgt in names and (src, tgt) not in existing:
                recovered.append(Edge(source=src, target=tgt, edge_type="call"))
                existing.add((src, tgt))
        return spec.model_copy(update={"edges": [*spec.edges, *recovered]})
