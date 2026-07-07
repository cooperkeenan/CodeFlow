from fastapi import APIRouter, Depends, File, Form, UploadFile

from dependencies import get_ci_ingest_service, get_current_user
from models.auth_model import AuthUser
from services.ci_ingest_service import CiIngestService

router = APIRouter(prefix="/ci", tags=["ci"])


@router.post("/analyse")
async def ci_analyse(
    repo: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_user),
    service: CiIngestService = Depends(get_ci_ingest_service),
) -> dict:
    await service.ingest(user.id, repo, file)
    return {"repo": repo, "source": "ci", "saved": True}
