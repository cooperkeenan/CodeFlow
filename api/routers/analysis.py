from core.config import Settings, get_settings
from dependencies import get_analysis_service
from fastapi import APIRouter, Depends
from models.analysis_model import AnalyseRequest, AnalyseResponse
from services.analysis_service import AnalysisService

from shared.models.profiler_response import ProfileResponse
from shared.models.tracer_request import TracerRequest

router = APIRouter(tags=["analysis"])


@router.post("/analyse", response_model=AnalyseResponse)
async def analyse(
    request: AnalyseRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalyseResponse:
    return await service.analyse(request)


@router.post("/analyse/local", response_model=AnalyseResponse)
async def analyse_local(
    service: AnalysisService = Depends(get_analysis_service),
    settings: Settings = Depends(get_settings),
) -> AnalyseResponse:
    request = AnalyseRequest(
        repo_name=settings.LOCAL_REPO_PATH.split("/")[-1],
        local_path=settings.LOCAL_REPO_PATH,
    )
    return await service.analyse(request)


@router.post("/analyse/from-profile", response_model=AnalyseResponse)
async def analyse_from_profile(
    profile: ProfileResponse,
    service: AnalysisService = Depends(get_analysis_service),
    settings: Settings = Depends(get_settings),
) -> AnalyseResponse:
    return await service.analyse_from_profile(
        repo_name=settings.LOCAL_REPO_PATH.split("/")[-1],
        local_path=settings.LOCAL_REPO_PATH,
        profile=profile,
    )


@router.post("/analyse/from-trace", response_model=AnalyseResponse)
async def analyse_from_trace(
    request: AnalyseResponse,
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalyseResponse:
    return await service.analyse_from_trace(request)