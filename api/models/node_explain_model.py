from pydantic import BaseModel


class NodeExplainRequest(BaseModel):
    node_id: str
