from fastapi import APIRouter, Depends
from profiler.dependencies import get_profiler_service
from profiler.models.profiler_model import ProfileRequest, ProfileResponse
from profiler.services.profiler_service import ProfilerService

router = APIRouter(tags=["profiler"])


@router.post("/profile", response_model=ProfileResponse)
async def profile(
    request: ProfileRequest,
    service: ProfilerService = Depends(get_profiler_service),
) -> ProfileResponse:
    return await service.profile(request)