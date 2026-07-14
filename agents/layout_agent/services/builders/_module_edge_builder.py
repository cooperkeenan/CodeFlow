from helpers.module_graph import ModuleGraph
from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import TemplateEdge


class ModuleEdgeBuilder:
    def real_edges(self, spec: DiagramSpec, graph: ModuleGraph) -> list[TemplateEdge]:
        comp_to_mod: dict[str, str] = {
            comp.name: module.name
            for module in spec.modules for comps in module.zones.values() for comp in comps
        }
        pairs: dict[frozenset, dict] = {}
        order: list[frozenset] = []
        for edge in spec.edges:
            src = comp_to_mod.get(edge.source)
            tgt = comp_to_mod.get(edge.target)
            if not src or not tgt or src == tgt:
                continue
            key: frozenset = frozenset({src, tgt})
            if key not in pairs:
                pairs[key] = {"src": src, "tgt": tgt, "type": edge.edge_type}
                order.append(key)
            elif edge.edge_type == "http" and pairs[key]["type"] != "http":
                pairs[key] = {"src": src, "tgt": tgt, "type": "http"}
        result = [
            TemplateEdge(source=pairs[k]["src"], target=pairs[k]["tgt"], edge_type=pairs[k]["type"])
            for k in order
        ]
        return sorted(result, key=lambda e: (e.source, e.target))

    def pipeline_edges(
        self, spec: DiagramSpec, graph: ModuleGraph, chain: list[str]
    ) -> list[TemplateEdge]:
        all_real = self.real_edges(spec, graph)
        chain_set = set(chain)
        in_chain = [e for e in all_real if e.source in chain_set and e.target in chain_set]
        covered: set[tuple[str, str]] = set()
        for e in in_chain:
            covered.add((e.source, e.target))
            covered.add((e.target, e.source))
        result = list(in_chain)
        for i in range(len(chain) - 1):
            src, tgt = chain[i], chain[i + 1]
            if (src, tgt) not in covered:
                result.append(TemplateEdge(source=src, target=tgt, edge_type="sequence"))
        return result
