import anthropic
import httpx
from core.config import Settings, get_settings
from fastapi import Depends

from services.cluster_planner import ClusterPlanner
from services.layout_service import LayoutService
from services.ownership_resolver import OwnershipResolver
from services.semantic_layout_service import SemanticLayoutService

from helpers.archetype_classifier import ArchetypeClassifier
from helpers.cluster_fallback import ClusterFallback
from helpers.cluster_validator import ClusterValidator
from helpers.component_metrics import ComponentMetricsBuilder
from helpers.importance_scorer import ImportanceScorer
from helpers.module_graph import ModuleGraphBuilder
from helpers.semantic_validator import SemanticValidator


def get_layout_service() -> LayoutService:
    return LayoutService(ModuleGraphBuilder(), ArchetypeClassifier())


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
