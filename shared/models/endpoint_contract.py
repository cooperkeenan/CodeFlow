from typing import Literal

from pydantic import BaseModel, Field


class ContractParam(BaseModel):
    name: str
    location: Literal["path", "query", "header", "body"]
    type: str = ""
    required: bool = False
    description: str = ""


class ContractResponse(BaseModel):
    status: str
    description: str = ""
    shape: str = ""


class EndpointContract(BaseModel):
    method: str
    path: str
    summary: str = ""
    params: list[ContractParam] = Field(default_factory=list)
    request_body: str = ""
    responses: list[ContractResponse] = Field(default_factory=list)
    auth: str = ""
    example_request: str = ""
    example_response: str = ""
    generated: bool = False


class KeyMethod(BaseModel):
    name: str
    fqn: str
    file: str = ""
    line: int = 0
    summary: str = ""


class EndpointDetail(BaseModel):
    id: str
    label: str
    method: str
    path: str
    title: str
    description: str = ""
    contract: EndpointContract
    methods: list[KeyMethod] = Field(default_factory=list)
    sources: dict[str, str] = Field(default_factory=dict)
