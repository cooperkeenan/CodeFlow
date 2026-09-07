from explain.models.contract_model import ContractRequest

from shared.flow_endpoints.handler_name import HandlerName
from shared.models.endpoint_contract import ContractParam, EndpointContract


class HeuristicContractWriter:
    def __init__(self, handler_name: HandlerName | None = None) -> None:
        self._handler_name_source = handler_name or HandlerName()

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
        return self._handler_name_source.humanize(name)
