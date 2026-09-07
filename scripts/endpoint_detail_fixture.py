import json
from pathlib import Path

from explain.models.contract_model import ContractRequest
from explain.services.contract.heuristic_contract_writer import HeuristicContractWriter

from shared.flow_endpoints.endpoint_detail_builder import EndpointDetailBuilder
from shared.flow_endpoints.endpoint_key_methods import KeyMethodSelector
from shared.flow_endpoints.entry_routes import EntryRoutes
from shared.flow_endpoints.handler_name import HandlerName
from shared.flow_endpoints.route_label import RouteLabel
from shared.models.endpoint_contract import EndpointContract
from shared.models.flow_graph import FlowGraph, FlowNode

_MAX_LINES = 120


class LocalSourceSlicer:
    def __init__(self, repo_path: Path | None) -> None:
        self._repo_path = repo_path
        self._cache: dict[str, list[str] | None] = {}

    def slice(self, span: dict) -> str:
        if self._repo_path is None:
            return ""
        file_path = span.get("file", "")
        if not file_path:
            return ""
        lines = self._lines_for(file_path)
        if lines is None:
            return ""
        start = max(span.get("line", 1) - 1, 0)
        end = min(span.get("end_line", start + 1), start + _MAX_LINES, len(lines))
        if start >= len(lines) or start >= end:
            return ""
        return "\n".join(lines[start:end])

    def _lines_for(self, file_path: str) -> list[str] | None:
        if file_path not in self._cache:
            full = self._repo_path / file_path
            try:
                self._cache[file_path] = full.read_text(encoding="utf-8").splitlines()
            except OSError:
                self._cache[file_path] = None
        return self._cache[file_path]


class EndpointDetailFixtureWriter:
    def __init__(self, repo_path: Path | None = None) -> None:
        self._key_methods = KeyMethodSelector()
        self._route_label = RouteLabel()
        self._builder = EndpointDetailBuilder(self._route_label)
        self._contract_writer = HeuristicContractWriter()
        self._slicer = LocalSourceSlicer(repo_path)
        self._routes = EntryRoutes(self._route_label)
        self._handler_name = HandlerName()

    def write(self, graph: FlowGraph, node: FlowNode, entry_id: str, target: Path) -> None:
        symbol_context = graph.meta.get("symbol_context", {})
        method_fqns = self._key_methods.select(graph, entry_id, symbol_context)
        sources = self._sources_for(method_fqns, symbol_context)
        default_fqn = symbol_context.get("nodes", {}).get(entry_id, "")
        contracts = [
            self._named(
                self._contract_writer.write(
                    ContractRequest(
                        entry_id=entry_id,
                        label=node.label,
                        method=route.method,
                        path=route.path,
                        handler_fqn=route.handler_fqn or default_fqn,
                        path_params=self._route_label.path_params(route.path),
                    )
                ),
                route.handler_fqn or default_fqn,
            )
            for route in self._routes.of(node)
        ]
        detail = self._builder.build(node, contracts, method_fqns, symbol_context, sources)
        payload = detail.model_dump(mode="json")
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _named(self, contract: EndpointContract, handler_fqn: str) -> EndpointContract:
        if not handler_fqn:
            return contract
        return contract.model_copy(update={"name": self._handler_name.humanize(handler_fqn)})

    def _sources_for(self, fqns: list[str], symbol_context: dict) -> dict[str, str]:
        functions = symbol_context.get("functions", {})
        classes = symbol_context.get("classes", {})
        sources: dict[str, str] = {}
        for fqn in fqns:
            entry = functions.get(fqn) or classes.get(fqn) or {}
            sources[fqn] = self._slicer.slice(entry.get("span", {}))
        return sources
