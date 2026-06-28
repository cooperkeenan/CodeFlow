from shared.models.diagram_template import DiagramType


class ComponentArchetypeClassifier:
    def classify(
        self,
        focus: str,
        callers: list[str],
        callees: list[str],
        children: list[str],
        all_comps: dict,
    ) -> DiagramType:
        n_callers = len(callers)
        n_callees = len(callees)
        n_children = len(children)

        if n_children >= 1 and self._subtree_depth(children, all_comps) >= 2:
            return "hierarchy"
        if n_callees + n_children >= 3 and n_callers <= 1:
            return "hub_and_spoke"
        if n_callers <= 1 and n_callees == 1 and n_children == 0:
            return "pipeline"
        return "relationship"

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
