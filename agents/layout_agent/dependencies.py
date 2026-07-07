import anthropic
import httpx
from core.config import Settings, get_settings
from core.template_config import TemplateLimitsConfig
from fastapi import Depends

from services.planning.cluster_planner import ClusterPlanner
from services.planning.layout_service import LayoutService
from services.planning.ownership_resolver import OwnershipResolver
from services.planning.semantic_layout_service import SemanticLayoutService
from services.planning.component_type_planner import ComponentTypePlanner
from services.planning.template_planner import TemplatePlanner
from services.planning.template_selector_service import TemplateSelectorService
from services.planning.view_planner import ViewPlanner

from helpers.archetype_classifier import ArchetypeClassifier
from helpers.cluster_fallback import ClusterFallback
from helpers.cluster_validator import ClusterValidator
from helpers.component_metrics import ComponentMetricsBuilder
from helpers.importance_scorer import ImportanceScorer
from helpers.module_graph import ModuleGraphBuilder
from helpers.semantic_validator import SemanticValidator

from templates.registry import TemplateRegistry
from tools.select_diagram_template_tool import SelectDiagramTemplateTool


def get_layout_service() -> LayoutService:
    return LayoutService(ModuleGraphBuilder(), ArchetypeClassifier())


def get_template_registry() -> TemplateRegistry:
    return TemplateRegistry(TemplateLimitsConfig())


def get_template_selector_service() -> TemplateSelectorService:
    return TemplateSelectorService(
        get_template_registry(),
        TemplateLimitsConfig(),
        ModuleGraphBuilder(),
    )


def get_select_diagram_template_tool(
    service: TemplateSelectorService = Depends(get_template_selector_service),
) -> SelectDiagramTemplateTool:
    return SelectDiagramTemplateTool(service)


def get_anthropic_client(
    settings: Settings = Depends(get_settings),
) -> anthropic.AsyncAnthropic:
    http_client = httpx.AsyncClient(verify=False)
    return anthropic.AsyncAnthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        http_client=http_client,
    )


def get_semantic_layout_service(
    anthropic_client: anthropic.AsyncAnthropic = Depends(get_anthropic_client),
) -> SemanticLayoutService:
    return SemanticLayoutService(
        anthropic_client,
        ComponentMetricsBuilder(),
        ImportanceScorer(),
        SemanticValidator(),
    )


def get_cluster_planner(
    anthropic_client: anthropic.AsyncAnthropic = Depends(get_anthropic_client),
) -> ClusterPlanner:
    return ClusterPlanner(
        anthropic_client,
        ComponentMetricsBuilder(),
        ClusterValidator(),
        ClusterFallback(),
    )


def get_ownership_resolver() -> OwnershipResolver:
    return OwnershipResolver(ComponentMetricsBuilder())


def get_template_planner(
    anthropic_client: anthropic.AsyncAnthropic = Depends(get_anthropic_client),
    tool: SelectDiagramTemplateTool = Depends(get_select_diagram_template_tool),
) -> TemplatePlanner:
    return TemplatePlanner(
        anthropic_client,
        tool,
        get_template_registry(),
    )


def get_component_type_planner(
    anthropic_client: anthropic.AsyncAnthropic = Depends(get_anthropic_client),
) -> ComponentTypePlanner:
    return ComponentTypePlanner(anthropic_client)


def get_view_planner(
    template_planner: TemplatePlanner = Depends(get_template_planner),
    comp_type_planner: ComponentTypePlanner = Depends(get_component_type_planner),
) -> ViewPlanner:
    return ViewPlanner(template_planner, comp_type_planner)
