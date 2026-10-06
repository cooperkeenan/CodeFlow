from tracer.services.analysis.routes.delegation_resolver import DelegationResolver


class RouteOwners:
    def __init__(self, delegates: DelegationResolver) -> None:
        self._delegates = delegates

    def of(self, handler_fqn: str) -> frozenset[str]:
        chain = {handler_fqn}
        current = self._delegates.resolve(handler_fqn)
        while current is not None and current not in chain:
            chain.add(current)
            current = self._delegates.resolve(current)
        return frozenset(chain)
