from typing import Literal

from pydantic import BaseModel

from models.symbol_slice import SymbolSlice


class ExplainRequest(BaseModel):
    node_id: str
    node_label: str = ""
    service: str = ""
    module: str = ""
    cls: str = ""
    focus_fqn: str
    symbols: list[SymbolSlice] = []
    helpers: list[SymbolSlice] = []


class MethodExplanation(BaseModel):
    name: str
    fqn: str
    summary: str


class HelperExplanation(BaseModel):
    name: str
    fqn: str
    summary: str


class NodeExplanation(BaseModel):
    node_id: str
    focus_fqn: str
    service: str
    primary_kind: Literal["class", "function"]
    primary_name: str
    primary_summary: str
    methods: list[MethodExplanation] = []
    helpers: list[HelperExplanation] = []
    generated: bool = False


class ExplainResponse(BaseModel):
    explanation: NodeExplanation
