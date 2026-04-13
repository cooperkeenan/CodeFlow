from core.config import Settings, get_settings
from dependencies import get_analysis_service
from fastapi import APIRouter, Depends
from models.analysis_model import AnalyseRequest, AnalyseResponse
from services.analysis_service import AnalysisService

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
        repo_name=settings.LOCAL_REPO_PATH.split("\\")[-1],
        local_path=settings.LOCAL_REPO_PATH,
    )
    return await service.analyse(request)