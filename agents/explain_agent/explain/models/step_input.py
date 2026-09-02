from pydantic import BaseModel


class StepInput(BaseModel):
    id: str
    kind: str
    raw: str
    label: str
    owner_fqn: str = ""
