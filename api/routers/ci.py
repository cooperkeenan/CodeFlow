from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from core.config import Settings, get_settings
from dependencies import (
    get_ci_ingest_service,
    get_current_user,
    get_local_ci_service,
)
from models.auth_model import AuthUser
from services.ci_ingest_service import CiIngestService
from services.local_ci_service import LocalCiService

router = APIRouter(prefix="/ci", tags=["ci"])


class LocalCiRequest(BaseModel):
    path: str | None = None


@router.post("/analyse")
async def ci_analyse(
    repo: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_user),
    service: CiIngestService = Depends(get_ci_ingest_service),
) -> dict:
    await service.ingest(user.id, repo, file)
    return {"repo": repo, "source": "ci", "saved": True}


@router.post("/analyse/local")
async def ci_analyse_local(
    request: LocalCiRequest,
    user: AuthUser = Depends(get_current_user),
    service: LocalCiService = Depends(get_local_ci_service),
    settings: Settings = Depends(get_settings),
) -> dict:
    path = request.path or settings.LOCAL_REPO_PATH
    result = await service.run(user.id, path)
    return {"repo": result.repo, "source": "ci-local", "saved": True}
