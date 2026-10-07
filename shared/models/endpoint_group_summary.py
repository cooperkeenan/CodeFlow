from pydantic import BaseModel


class EndpointGroupSummary(BaseModel):
    id: str
    parent_id: str | None = None
    name: str
    route_count: int
    is_leaf: bool
    depth: int = 0
