import re

from explain.models.contract_model import ContractRequest

from shared.models.endpoint_contract import ContractParam, EndpointContract

_SPLIT_PATTERN = re.compile(r"[_\s]+")


class HeuristicContractWriter:
    def write(self, request: ContractRequest) -> EndpointContract:
        params = [
            ContractParam(name=name, location="path", required=True)
            for name in request.path_params
        ]
        return EndpointContract(
            method=request.method,
            path=request.path,
            summary=self._summary(request),
            params=params,
            generated=False,
        )

    def _summary(self, request: ContractRequest) -> str:
        name = self._handler_name(request)
        if not name:
            return ""
        return self._humanize(name)

    def _handler_name(self, request: ContractRequest) -> str:
        if request.handler_fqn:
            return request.handler_fqn.rsplit(".", 1)[-1]
        return request.label

    def _humanize(self, name: str) -> str:
        words = [w for w in _SPLIT_PATTERN.split(name) if w]
        if not words:
            return name
        sentence = " ".join(words).lower()
        return sentence[0].upper() + sentence[1:]
