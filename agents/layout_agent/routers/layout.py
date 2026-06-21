from fastapi import APIRouter, Depends

from dependencies import (
    get_cluster_planner,
    get_layout_service,
    get_ownership_resolver,
    get_semantic_layout_service,
    get_view_planner,
)
from models.layout_model import LayoutRequest, LayoutResponse
from services.cluster_planner import ClusterPlanner
from services.layout_service import LayoutService
from services.ownership_resolver import OwnershipResolver
from services.semantic_layout_service import SemanticLayoutService
from services.view_planner import ViewPlanner

router = APIRouter(tags=["layout"])


@router.post("/layout", response_model=LayoutResponse)
async def layout(
    request: LayoutRequest,
    service: LayoutService = Depends(get_layout_service),
    semantic: SemanticLayoutService = Depends(get_semantic_layout_service),
    cluster_planner: ClusterPlanner = Depends(get_cluster_planner),
    resolver: OwnershipResolver = Depends(get_ownership_resolver),
    view_planner: ViewPlanner = Depends(get_view_planner),
) -> LayoutResponse:
    resolver.resolve(request.diagram_spec)
    hint = service.layout(request.diagram_spec)
    spec = await semantic.enrich(request.diagram_spec)
    plan_result = await cluster_planner.plan(spec)
    spec = plan_result.spec
    spec.layout_hint = hint
    diagram_templates = await view_planner.plan(spec, plan_result.module_types, plan_result.module_rationales)
    return LayoutResponse(layout_hint=hint, diagram_spec=spec, diagram_templates=diagram_templates)
