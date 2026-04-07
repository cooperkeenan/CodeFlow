from fastapi import APIRouter, Depends

from dependencies import get_analysis_service
from models.analysis_model import AnalyseRequest, AnalyseResponse
from services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])


@router.post("/analyse", response_model=AnalyseResponse)
async def analyse(
    request: AnalyseRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalyseResponse:
    return await service.analyse(request)