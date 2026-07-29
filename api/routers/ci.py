import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from core.config import Settings, get_settings
from dependencies import (
    get_ci_ingest_service,
    get_current_user,
    get_github_ci_service,
    get_local_ci_service,
    get_progress_tracker,
)
from models.auth_model import AuthUser
from services.ci_ingest_service import CiIngestService
from services.github_ci_service import GitHubCiService
from services.local_ci_service import LocalCiService
from services.progress_tracker import ProgressTracker

router = APIRouter(prefix="/ci", tags=["ci"])


class LocalCiRequest(BaseModel):
    path: str | None = None


class GithubCiRequest(BaseModel):
    repo_name: str


@router.post("/analyse")
async def ci_analyse(
    repo: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_user),
    service: CiIngestService = Depends(get_ci_ingest_service),
) -> dict:
    await service.ingest(user.id, repo, file)
    return {"repo": repo, "source": "ci", "saved": True}


@router.get("/progress")
async def ci_progress(progress: ProgressTracker = Depends(get_progress_tracker)) -> dict:
    return progress.snapshot()


@router.post("/analyse/local")
async def ci_analyse_local(
    http_request: Request,
    request: LocalCiRequest,
    user: AuthUser = Depends(get_current_user),
    service: LocalCiService = Depends(get_local_ci_service),
    settings: Settings = Depends(get_settings),
    progress: ProgressTracker = Depends(get_progress_tracker),
) -> dict:
    path = request.path or settings.LOCAL_REPO_PATH
    if not path or not Path(path).is_dir():
        raise HTTPException(status_code=400, detail=f"Local path not found: {path}")
    if progress.snapshot()["active"]:
        return {"started": False, "busy": True}
    progress.start()
    http_request.app.state.analysis_task = asyncio.create_task(service.run_background(user.id, path))
    return {"started": True}


@router.post("/analyse/github")
async def ci_analyse_github(
    http_request: Request,
    request: GithubCiRequest,
    user: AuthUser = Depends(get_current_user),
    service: GitHubCiService = Depends(get_github_ci_service),
    progress: ProgressTracker = Depends(get_progress_tracker),
) -> dict:
    if progress.snapshot()["active"]:
        return {"started": False, "busy": True}
    progress.start()
    http_request.app.state.analysis_task = asyncio.create_task(
        service.run_background(user.id, request.repo_name)
    )
    return {"started": True}
