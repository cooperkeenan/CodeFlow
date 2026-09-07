from explain.models.symbol_slice import SymbolSlice
from pydantic import BaseModel, Field

from shared.models.endpoint_contract import EndpointContract


class ContractRequest(BaseModel):
    entry_id: str
    label: str
    method: str = ""
    path: str = ""
    handler_fqn: str = ""
    path_params: list[str] = Field(default_factory=list)
    symbols: list[SymbolSlice] = Field(default_factory=list)
    helpers: list[SymbolSlice] = Field(default_factory=list)


class ContractResponse(BaseModel):
    contract: EndpointContract
