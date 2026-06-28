import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from core.config import Settings, get_settings
from dependencies import get_analysis_service
from models.analysis_model import AnalyseRequest, AnalyseResponse
from services.analysis_service import AnalysisService

from shared.models.profiler_response import ProfileResponse

router = APIRouter(tags=["analysis"])

_OUTPUTS_DIR = Path(__file__).resolve().parents[2] / "shared" / "outputs"


@router.post("/analyse", response_model=AnalyseResponse)
async def analyse(
    request: AnalyseRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalyseResponse:
    result = await service.analyse(request)
    (_OUTPUTS_DIR / "tracer_output.json").write_text(result.model_dump_json(indent=2))
    return result


@router.post("/analyse/local", response_model=AnalyseResponse)
async def analyse_local(
    service: AnalysisService = Depends(get_analysis_service),
    settings: Settings = Depends(get_settings),
) -> AnalyseResponse:
    result = await service.analyse(AnalyseRequest(
        repo_name=Path(settings.LOCAL_REPO_PATH).name,
        local_path=settings.LOCAL_REPO_PATH,
    ))
    (_OUTPUTS_DIR / "tracer_output.json").write_text(result.model_dump_json(indent=2))
    return result


@router.post("/analyse/local/from-profile", response_model=AnalyseResponse)
async def analyse_local_from_profile(
    service: AnalysisService = Depends(get_analysis_service),
    settings: Settings = Depends(get_settings),
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
    return result


@router.post("/analyse/local/from-trace", response_model=AnalyseResponse)
async def analyse_local_from_trace(
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalyseResponse:
    path = _OUTPUTS_DIR / "tracer_output.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No stored tracer output")
    stored = AnalyseResponse.model_validate(json.loads(path.read_text()))
    result = await service.analyse_from_trace(stored)
    (_OUTPUTS_DIR / "tracer_output.json").write_text(result.model_dump_json(indent=2))
    return result