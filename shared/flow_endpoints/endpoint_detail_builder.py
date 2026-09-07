from shared.flow_endpoints.route_label import RouteLabel
from shared.models.endpoint_contract import EndpointContract, EndpointDetail, KeyMethod
from shared.models.flow_graph import FlowNode


class EndpointDetailBuilder:
    def __init__(self, route_label: RouteLabel | None = None) -> None:
        self._route_label = route_label or RouteLabel()

    def build(
        self,
        node: FlowNode,
        contract: EndpointContract,
        method_fqns: list[str],
        symbol_context: dict,
        sources: dict[str, str],
    ) -> EndpointDetail:
        method, path = self._route_label.parse(node.label)
        return EndpointDetail(
            id=node.id,
            label=node.label,
            method=method,
            path=path,
            title=node.llm_label or node.label,
            description=node.one_liner,
            contract=contract,
            methods=[self._key_method(fqn, symbol_context) for fqn in method_fqns],
            sources={fqn: source for fqn, source in sources.items() if fqn in method_fqns},
        )

    def _key_method(self, fqn: str, symbol_context: dict) -> KeyMethod:
        functions = symbol_context.get("functions", {})
        classes = symbol_context.get("classes", {})
        entry = functions.get(fqn) or classes.get(fqn) or {}
        span = entry.get("span", {})
        return KeyMethod(
            name=entry.get("name", fqn.rsplit(".", 1)[-1]),
            fqn=fqn,
            file=span.get("file", ""),
            line=span.get("line", 0),
        )
