import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from core.config import Settings, get_settings
from dependencies import (
    get_analysis_service,
    get_optional_user,
    get_repo_map_service,
    get_stage_status_service,
)
from models.analysis_model import AnalyseRequest, AnalyseResponse
from models.auth_model import AuthUser
from services.analysis_service import AnalysisService
from services.repo_map_service import RepoMapService
from services.stage_status_service import StageStatusService

from shared.models.profiler_response import ProfileResponse

router = APIRouter(tags=["analysis"])

_OUTPUTS_DIR = Path(__file__).resolve().parents[2] / "shared" / "outputs"


@router.post("/analyse", response_model=AnalyseResponse)
async def analyse(
    request: AnalyseRequest,
    service: AnalysisService = Depends(get_analysis_service),
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    user: AuthUser | None = Depends(get_optional_user),
) -> AnalyseResponse:
    result = await service.analyse(request)
    (_OUTPUTS_DIR / "tracer_output.json").write_text(result.model_dump_json(indent=2))
    if user is not None:
        await repo_map_service.save(user.id, result, source="web")
    return result


@router.get("/analyse/stage-status")
async def analyse_stage_status(
    svc: StageStatusService = Depends(get_stage_status_service),
) -> dict:
    return svc.get_recommendation()


@router.post("/analyse/local", response_model=AnalyseResponse)
async def analyse_local(
    service: AnalysisService = Depends(get_analysis_service),
    settings: Settings = Depends(get_settings),
    stage_status: StageStatusService = Depends(get_stage_status_service),
) -> AnalyseResponse:
    result = await service.analyse(AnalyseRequest(
        repo_name=Path(settings.LOCAL_REPO_PATH).name,
        local_path=settings.LOCAL_REPO_PATH,
    ))
    (_OUTPUTS_DIR / "tracer_output.json").write_text(result.model_dump_json(indent=2))
    stage_status.record_run("profiler")
    return result


@router.post("/analyse/local/from-profile", response_model=AnalyseResponse)
async def analyse_local_from_profile(
    service: AnalysisService = Depends(get_analysis_service),
    settings: Settings = Depends(get_settings),
    stage_status: StageStatusService = Depends(get_stage_status_service),
) -> AnalyseResponse:
    path = _OUTPUTS_DIR / "profiler_output.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No stored profiler output")
    profile = ProfileResponse.model_validate(json.loads(path.read_text()))
    result = await service.analyse_from_profile(
        repo_name=Path(settings.LOCAL_REPO_PATH).name,
        local_path=settings.LOCAL_REPO_PATH,
        profile=profile,
    )
    (_OUTPUTS_DIR / "tracer_output.json").write_text(result.model_dump_json(indent=2))
    stage_status.record_run("tracer")
    return result


@router.post("/analyse/local/from-trace", response_model=AnalyseResponse)
async def analyse_local_from_trace(
    service: AnalysisService = Depends(get_analysis_service),
    stage_status: StageStatusService = Depends(get_stage_status_service),
) -> AnalyseResponse:
    path = _OUTPUTS_DIR / "tracer_output.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No stored tracer output")
    stored = AnalyseResponse.model_validate(json.loads(path.read_text()))
    result = await service.analyse_from_trace(stored)
    (_OUTPUTS_DIR / "tracer_output.json").write_text(result.model_dump_json(indent=2))
    stage_status.record_run("layout")
    return result


@router.post("/analyse/local/from-layout", response_model=AnalyseResponse)
async def analyse_local_from_layout(
    service: AnalysisService = Depends(get_analysis_service),
    stage_status: StageStatusService = Depends(get_stage_status_service),
) -> AnalyseResponse:
    layout_path = _OUTPUTS_DIR / "layout.json"
    trace_path = _OUTPUTS_DIR / "tracer_output.json"
    if not layout_path.exists():
        raise HTTPException(status_code=404, detail="No stored layout output")
    if not trace_path.exists():
        raise HTTPException(status_code=404, detail="No stored tracer output")
    stored_layout = json.loads(layout_path.read_text())
    diagram_templates = stored_layout.get("diagram_templates")
    if not diagram_templates:
        raise HTTPException(status_code=422, detail="Stored layout has no diagram_templates")
    stored = AnalyseResponse.model_validate(json.loads(trace_path.read_text()))
    result = await service.analyse_from_layout(stored, diagram_templates)
    trace_path.write_text(result.model_dump_json(indent=2))
    stage_status.record_run("render")
    return result