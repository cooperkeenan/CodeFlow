from shared.models.diagram_template import DiagramType

_HUB_MIN_SPOKES = 4


class ComponentArchetypeClassifier:
    def classify(
        self,
        focus: str,
        callers: list[str],
        callees: list[str],
        children: list[str],
        all_comps: dict,
        comp_to_mod: dict[str, str],
        edges: list,
    ) -> DiagramType:
        n_callers = len(callers)
        n_callees = len(callees)
        n_children = len(children)
        steps = [*callees, *children]
        if n_callers <= 1 and self.is_api_hub(focus, steps, comp_to_mod, edges):
            return "hub_and_spoke"
        if n_children >= 1 and self._subtree_depth(children, all_comps) >= 2:
            return "hierarchy"
        if n_callers <= 1 and len(steps) >= 3:
            return "hierarchy"
        if n_callers <= 1 and n_callees == 1 and n_children == 0:
            return "pipeline"
        return "relationship"

    def is_api_hub(self, focus: str, steps: list[str], comp_to_mod: dict[str, str], edges: list) -> bool:
        if len(steps) < _HUB_MIN_SPOKES:
            return False
        step_set = set(steps)
        focus_mod = comp_to_mod.get(focus)
        spoke_mods = {comp_to_mod.get(s) for s in steps} - {focus_mod, None}
        http_spokes = sum(1 for e in edges if e.source == focus and e.target in step_set and e.edge_type == "http")
        inter_spoke = sum(1 for e in edges if e.source in step_set and e.target in step_set and e.source != e.target)
        cross_service = len(spoke_mods) >= 3 or http_spokes >= 3
        return cross_service and inter_spoke == 0

    def _subtree_depth(self, children: list[str], all_comps: dict) -> int:
        if not children:
            return 0
        depth = 1
        for name in children:
            comp = all_comps.get(name)
            if comp and comp.children:
                grandchildren = [c for c in comp.children if c in all_comps]
                if grandchildren:
                    depth = max(depth, 1 + self._subtree_depth(grandchildren, all_comps))
        return depth
