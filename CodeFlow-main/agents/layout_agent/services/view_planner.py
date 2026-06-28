import logging

from helpers.component_archetype_classifier import ComponentArchetypeClassifier
from services._view_builder import _ViewBuilder
from services.component_type_planner import ComponentTypePlanner
from services.template_planner import TemplatePlanner
from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import DiagramTemplate

logger = logging.getLogger(__name__)


class ViewPlanner:
    def __init__(self, template_planner: TemplatePlanner, comp_type_planner: ComponentTypePlanner) -> None:
        self._template_planner = template_planner
        self._comp_type_planner = comp_type_planner
        self._builder = _ViewBuilder(ComponentArchetypeClassifier())

    async def plan(
        self, spec: DiagramSpec, module_types: dict[str, str],
        module_rationales: dict[str, str] | None = None,
    ) -> dict[str, DiagramTemplate]:
        system = await self._template_planner.plan(spec)
        views: dict[str, DiagramTemplate] = {"system": system}
        logger.info("ViewPlanner: system type=%s", system.type)

        view_set = self._view_set(spec)
        comp_types = await self._comp_type_planner.plan(spec, view_set)

        for module in spec.modules:
            diagram_type = module_types.get(module.name, "dependency_graph")
            template = self._builder.build_module(spec, module, diagram_type, view_set)
            rationale = (module_rationales or {}).get(module.name, "")
            if rationale:
                template = template.model_copy(update={"meta": {**template.meta, "rationale": rationale}})
            views[f"module:{module.name}"] = template

        for comp_name in sorted(view_set):
            views[f"component:{comp_name}"] = self._builder.build_component(
                spec, comp_name, view_set, comp_types
            )

        logger.info(
            "ViewPlanner: %d views (1 system, %d module, %d component)",
            len(views), len(spec.modules), len(view_set),
        )
        return views

    def _view_set(self, spec: DiagramSpec) -> set[str]:
        call_names: set[str] = set()
        for e in spec.edges:
            if e.edge_type != "import":
                call_names.add(e.source)
                call_names.add(e.target)
        return {
            c.name
            for m in spec.modules
            for cs in m.zones.values()
            for c in cs
            if c.children or c.name in call_names
        }
