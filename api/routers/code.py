from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import get_code_read_service
from services.code_read_service import CodeReadService


class CodeResponse(BaseModel):
    file_path: str
    language: str
    content: str


router = APIRouter(tags=["code"])


@router.get("/code", response_model=CodeResponse)
async def get_code(
    repo: str,
    path: str,
    service: CodeReadService = Depends(get_code_read_service),
) -> CodeResponse:
    result = await service.get_code(repo, path)
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return CodeResponse(**result)
