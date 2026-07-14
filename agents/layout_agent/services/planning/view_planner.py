import logging

from helpers.component_archetype_classifier import ComponentArchetypeClassifier
from models.hierarchy import HierarchyPlan
from models.service_step import ServiceStepPlan
from services.builders._service_view_builder import _ServiceViewBuilder
from services.builders._view_builder import _ViewBuilder
from services.planning.component_type_planner import ComponentTypePlanner
from services.planning.hierarchy_classifier import HierarchyClassifier
from services.planning.service_step_planner import ServiceStepPlanner
from services.planning.template_planner import TemplatePlanner
from shared.models.diagram_spec import DiagramSpec, Module
from shared.models.diagram_template import DiagramTemplate

logger = logging.getLogger(__name__)


class ViewPlanner:
    def __init__(
        self,
        template_planner: TemplatePlanner,
        comp_type_planner: ComponentTypePlanner,
        hierarchy: HierarchyClassifier,
        service_planner: ServiceStepPlanner,
        service_builder: _ServiceViewBuilder,
    ) -> None:
        self._template_planner = template_planner
        self._comp_type_planner = comp_type_planner
        self._hierarchy = hierarchy
        self._service_planner = service_planner
        self._service_builder = service_builder
        self._builder = _ViewBuilder(ComponentArchetypeClassifier())

    async def plan(
        self, spec: DiagramSpec, module_types: dict[str, str],
        module_rationales: dict[str, str] | None = None,
    ) -> dict[str, DiagramTemplate]:
        hplan = self._hierarchy.classify(spec)
        arch_names = set(hplan.architecture_modules)
        scoped = spec.model_copy(update={"modules": [m for m in spec.modules if m.name in arch_names]})
        system = await self._template_planner.plan(scoped)
        views: dict[str, DiagramTemplate] = {"system": system}
        logger.info("ViewPlanner: system type=%s", system.type)

        view_set = self._view_set(spec)
        service_pairs = await self._gather_service_plans(spec, hplan, view_set)

        for module, step_plan in service_pairs:
            template = self._service_builder.build(step_plan, module, view_set)
            fallback = (module_rationales or {}).get(module.name, "")
            if fallback and not step_plan.purpose:
                template = template.model_copy(update={"meta": {**template.meta, "rationale": fallback}})
            views[f"module:{module.name}"] = template

        comp_types = await self._comp_type_planner.plan(spec, view_set)
        for comp_name in sorted(view_set):
            views[f"component:{comp_name}"] = self._builder.build_component(
                spec, comp_name, view_set, comp_types
            )

        logger.info(
            "ViewPlanner: %d views (1 system, %d module, %d component)",
            len(views), len(service_pairs), len(view_set),
        )
        return views

    async def _gather_service_plans(
        self, spec: DiagramSpec, hplan: HierarchyPlan, view_set: set[str],
    ) -> list[tuple[Module, ServiceStepPlan]]:
        service_names = set(hplan.service_modules)
        pairs: list[tuple[Module, ServiceStepPlan]] = []
        for module in spec.modules:
            if module.name not in service_names:
                continue
            step_plan = await self._service_planner.plan(spec, module)
            for step in step_plan.steps:
                if step.backing_components:
                    view_set.add(step.backing_components[0])
            pairs.append((module, step_plan))
        return pairs

    def _view_set(self, spec: DiagramSpec) -> set[str]:
        call_names: set[str] = set()
        for e in spec.edges:
            if e.edge_type != "import":
                call_names.add(e.source)
                call_names.add(e.target)
        all_comps = [c for m in spec.modules for cs in m.zones.values() for c in cs]
        deps: dict[str, set[str]] = {}
        for c in all_comps:
            deps[c.name] = set(c.children or [])
        for e in spec.edges:
            if e.edge_type != "import" and e.source != e.target:
                deps.setdefault(e.source, set()).add(e.target)
        return {
            c.name
            for c in all_comps
            if (c.children or c.name in call_names) and len(deps.get(c.name, set())) != 1
        }
