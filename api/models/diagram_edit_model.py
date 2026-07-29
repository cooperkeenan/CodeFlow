from pydantic import BaseModel


class DiagramEditsResponse(BaseModel):
    repo: str
    edits: dict


class DiagramEditsPutRequest(BaseModel):
    edits: dict
