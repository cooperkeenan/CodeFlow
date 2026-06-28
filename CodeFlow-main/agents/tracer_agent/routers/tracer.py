from dependencies import get_tracer_service
from fastapi import APIRouter, Depends
from models.tracer_model import TracerResponse
from services.tracer_service import TracerService

from shared.models.tracer_request import TracerRequest

router = APIRouter(tags=["tracer"])


@router.post("/trace", response_model=TracerResponse)
async def trace(
    request: TracerRequest,
    service: TracerService = Depends(get_tracer_service),
) -> TracerResponse:
    return await service.trace(request)