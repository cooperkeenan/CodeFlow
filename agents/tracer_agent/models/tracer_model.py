from pydantic import BaseModel


class TracerResponse(BaseModel):
    architecture_type: str
    description: str