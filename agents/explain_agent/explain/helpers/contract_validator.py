from explain.models.contract_model import ContractRequest

from shared.models.endpoint_contract import EndpointContract

_MAX_PARAMS = 30
_MAX_RESPONSES = 12
_MAX_SUMMARY_CHARS = 400
_MAX_DESCRIPTION_CHARS = 300
_ALLOWED_LOCATIONS = {"path", "query", "header", "body"}


class ContractValidator:
    def validate(self, contract: EndpointContract, request: ContractRequest) -> bool:
        if contract.method != request.method:
            return False
        if contract.path != request.path:
            return False
        if len(contract.params) > _MAX_PARAMS:
            return False
        if len(contract.responses) > _MAX_RESPONSES:
            return False
        if len(contract.summary) > _MAX_SUMMARY_CHARS:
            return False
        for param in contract.params:
            if param.location not in _ALLOWED_LOCATIONS:
                return False
            if len(param.description) > _MAX_DESCRIPTION_CHARS:
                return False
        for response in contract.responses:
            if len(response.description) > _MAX_DESCRIPTION_CHARS:
                return False
        return True
