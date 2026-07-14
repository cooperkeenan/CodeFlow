import logging
from dataclasses import dataclass

from core.template_config import TemplateLimitsConfig
from helpers.module_graph import ModuleGraphBuilder
from services.builders._module_edge_builder import ModuleEdgeBuilder
from services.builders._template_builder import _TemplateBuilder
from services.builders._template_meta_builder import _TemplateMetaBuilder
from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import DiagramTemplate, DiagramType
from templates.registry import TemplateRegistry

logger = logging.getLogger(__name__)

_FALLBACK: dict[str, DiagramType] = {
    "pipeline": "dependency_graph",
    "hub_and_spoke": "dependency_graph",
    "layered_tier": "dependency_graph",
    "hierarchy": "dependency_graph",
    "dependency_graph": "mesh",
}


@dataclass
class SelectionResult:
    ok: bool
    template: DiagramTemplate | None
    limit_hit: str | None
    actual_count: int | None
    suggested_type: DiagramType | None


class TemplateSelectorService:
    def __init__(
        self,
        registry: TemplateRegistry,
        config: TemplateLimitsConfig,
        graph_builder: ModuleGraphBuilder,
    ) -> None:
        self._registry = registry
        self._config = config
        self._graph_builder = graph_builder
        self._builder = _TemplateBuilder(_TemplateMetaBuilder(), ModuleEdgeBuilder())

    def select(
        self,
        diagram_type: DiagramType,
        spec: DiagramSpec,
        pipeline_order: list[str] | None = None,
    ) -> SelectionResult:
        graph = self._graph_builder.build(spec)
        defn = self._registry.get(diagram_type)
        node_count = len(graph.module_names)

        if diagram_type == "hierarchy" and defn.max_depth is not None:
            depth = self._builder.compute_depth(graph)
            if depth > defn.max_depth:
                return SelectionResult(
                    ok=False,
                    template=None,
                    limit_hit="hierarchy.max_depth",
                    actual_count=depth,
                    suggested_type="dependency_graph",
                )

        if node_count > defn.node_limit:
            if diagram_type == "mesh":
                logger.warning(
                    "mesh overflow: %d nodes exceeds limit %d; building anyway",
                    node_count,
                    defn.node_limit,
                )
                return SelectionResult(
                    ok=True,
                    template=self._builder.build(diagram_type, spec, graph, pipeline_order),
                    limit_hit=None,
                    actual_count=node_count,
                    suggested_type=None,
                )
            return SelectionResult(
                ok=False,
                template=None,
                limit_hit=f"{diagram_type}.node_limit",
                actual_count=node_count,
                suggested_type=_FALLBACK.get(diagram_type, "mesh"),
            )

        return SelectionResult(
            ok=True,
            template=self._builder.build(diagram_type, spec, graph, pipeline_order),
            limit_hit=None,
            actual_count=node_count,
            suggested_type=None,
        )
