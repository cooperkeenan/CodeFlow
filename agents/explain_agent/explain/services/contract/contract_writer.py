from typing import Protocol

from explain.models.contract_model import ContractRequest

from shared.models.endpoint_contract import EndpointContract


class ContractWriter(Protocol):
    def write(self, request: ContractRequest) -> EndpointContract: ...
