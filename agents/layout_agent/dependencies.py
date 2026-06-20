import anthropic
import httpx
from core.config import Settings, get_settings
from core.template_config import TemplateLimitsConfig
from fastapi import Depends

from services.cluster_planner import ClusterPlanner
from services.layout_service import LayoutService
from services.ownership_resolver import OwnershipResolver
from services.semantic_layout_service import SemanticLayoutService
from services.template_planner import TemplatePlanner
from services.template_selector_service import TemplateSelectorService
from services.view_planner import ViewPlanner

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
        ArchetypeClassifier(),
        get_template_registry(),
        ModuleGraphBuilder(),
    )


def get_view_planner(
    template_planner: TemplatePlanner = Depends(get_template_planner),
) -> ViewPlanner:
    return ViewPlanner(template_planner)
