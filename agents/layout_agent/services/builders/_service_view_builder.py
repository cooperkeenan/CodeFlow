from models.service_step import ServiceStep, ServiceStepPlan
from shared.models.diagram_spec import Module
from shared.models.diagram_template import DiagramTemplate, TemplateEdge, TemplateNode

_CALL = "call"
_SEQ = "sequence"


class _ServiceViewBuilder:
    def build(self, plan: ServiceStepPlan, module: Module, view_set: set[str]) -> DiagramTemplate:
        sorted_steps = sorted(plan.steps, key=lambda s: s.order_index)
        nodes = self._nodes(sorted_steps, module, view_set)
        step_ids = [n.id for n in nodes]
        edges = self._edges(plan.diagram_type, step_ids)
        meta = self._meta(plan, step_ids)
        return DiagramTemplate(type=plan.diagram_type, nodes=nodes, edges=edges, meta=meta)

    def _nodes(
        self, steps: list[ServiceStep], module: Module, view_set: set[str]
    ) -> list[TemplateNode]:
        nodes: list[TemplateNode] = []
        for i, step in enumerate(steps):
            step_id = f"step__{module.name}__{i}"
            drillable = bool(step.backing_components) and step.backing_components[0] in view_set
            nodes.append(TemplateNode(
                id=step_id,
                label=step.label,
                description="",
                module_name=module.name,
                tier="primary",
                kind="component",
                backing_components=list(step.backing_components),
                drillable=drillable,
                style="focus" if i == 0 else None,
            ))
        return nodes

    def _edges(self, diagram_type: str, step_ids: list[str]) -> list[TemplateEdge]:
        if not step_ids:
            return []
        if diagram_type in ("pipeline", "dependency_graph"):
            return [
                TemplateEdge(source=step_ids[i], target=step_ids[i + 1], edge_type=_SEQ)
                for i in range(len(step_ids) - 1)
            ]
        first = step_ids[0]
        return [
            TemplateEdge(source=first, target=step_ids[i], edge_type=_CALL)
            for i in range(1, len(step_ids))
        ]

    def _meta(self, plan: ServiceStepPlan, step_ids: list[str]) -> dict:
        first = step_ids[0] if step_ids else ""
        depth_map = {sid: (0 if j == 0 else 1) for j, sid in enumerate(step_ids)}
        return {
            "focus": first,
            "hub_id": first,
            "depth_map": depth_map,
            "order": step_ids,
            "rationale": plan.purpose,
        }
