from datetime import datetime

from gateway.services.endpoint_contract_resolver import EndpointContractResolver
from gateway.services.endpoint_view_cache import EndpointViewCache
from gateway.services.flow_graph_cache import FlowGraphCache
from gateway.services.group_detail_scope import GroupDetailScope
from gateway.services.repo_map_service import RepoMapService
from gateway.services.symbol_context_resolver import SymbolContextResolver

from shared.flow_endpoints.endpoint_detail_builder import EndpointDetailBuilder
from shared.flow_endpoints.endpoint_group import EndpointGroup
from shared.flow_endpoints.endpoint_group_tree import EndpointGroupTree
from shared.flow_endpoints.endpoint_key_methods import KeyMethodSelector
from shared.flow_endpoints.entry_routes import EntryRoutes
from shared.flow_endpoints.handler_name import HandlerName
from shared.flow_endpoints.route_label import RouteLabel
from shared.models.endpoint_contract import EndpointDetail
from shared.models.flow_graph import FlowGraph, FlowNode


class EndpointDetailService:
    def __init__(
        self,
        repo_map_service: RepoMapService,
        resolver: SymbolContextResolver,
        contract_resolver: EndpointContractResolver,
        graph_cache: FlowGraphCache,
        view_cache: EndpointViewCache,
        key_method_selector: KeyMethodSelector,
        route_label: RouteLabel,
        detail_builder: EndpointDetailBuilder,
        group_tree: EndpointGroupTree,
        group_scope: GroupDetailScope,
    ) -> None:
        self._repo_maps = repo_map_service
        self._resolver = resolver
        self._contracts = contract_resolver
        self._graph_cache = graph_cache
        self._view_cache = view_cache
        self._key_methods = key_method_selector
        self._route_label = route_label
        self._builder = detail_builder
        self._group_tree = group_tree
        self._group_scope = group_scope
        self._routes = EntryRoutes(route_label)
        self._handler_name = HandlerName()

    async def detail(self, user_id: int, repo: str, entry_id: str) -> dict | None:
        resolved = await self._resolve(user_id, repo)
        if resolved is None:
            return None
        graph, updated_at = resolved
        forest = self._group_tree.build(graph)
        group = forest.find(entry_id)
        real_id = group.entry_id if group else entry_id
        node = self._find_entry(graph, real_id)
        if node is None:
            return None

        view_key = f"detail:{entry_id}"
        cached = self._view_cache.get(user_id, repo, updated_at, view_key)
        if cached is not None:
            return cached

        symbol_context = graph.meta.get("symbol_context")
        if symbol_context is None:
            return None

        built = await self._build_payload(graph, node, real_id, repo, symbol_context, group)
        if group is not None:
            built = self._group_scope.apply(built, forest, group)
        payload = built.model_dump(mode="json")
        self._view_cache.put(user_id, repo, updated_at, view_key, payload)
        return payload

    async def _build_payload(
        self,
        graph: FlowGraph,
        node: FlowNode,
        entry_id: str,
        repo: str,
        symbol_context: dict,
        group: EndpointGroup | None,
    ) -> EndpointDetail:
        functions = symbol_context.get("functions", {})
        classes = symbol_context.get("classes", {})
        method_fqns = self._key_methods.select(graph, entry_id, symbol_context)
        routes = self._routes.of(node)
        if group is not None:
            routes = self._group_scope.routes(routes, group) if group.is_leaf else []

        file_cache: dict[str, dict | None] = {}
        fetch_fqns = method_fqns + [r.handler_fqn for r in routes if r.handler_fqn]
        sources = await self._sources_for(
            list(dict.fromkeys(fetch_fqns)), functions, classes, repo, file_cache
        )

        contracts = []
        for route in routes:
            contract = await self._contracts.resolve(
                entry_id, node, route.method, route.path,
                self._route_label.path_params(route.path),
                sources, symbol_context, repo, route.handler_fqn,
            )
            if route.handler_fqn:
                contract = contract.model_copy(
                    update={
                        "name": self._handler_name.humanize(route.handler_fqn),
                        "handler_fqn": route.handler_fqn,
                    }
                )
            contracts.append(contract)
        detail = self._builder.build(node, contracts, method_fqns, symbol_context, sources)
        return detail

    async def _sources_for(
        self, fqns: list[str], functions: dict, classes: dict, repo: str, file_cache: dict
    ) -> dict[str, str]:
        slices = [
            await self._resolver.slice_for(fqn, functions, classes, repo, file_cache) for fqn in fqns
        ]
        return {s["fqn"]: s["source"] for s in slices if s is not None}

    async def _resolve(self, user_id: int, repo: str) -> tuple[FlowGraph, datetime] | None:
        updated_at = await self._repo_maps.updated_at(user_id, repo)
        if updated_at is None:
            return None
        graph = await self._graph(user_id, repo, updated_at)
        if graph is None:
            return None
        return graph, updated_at

    async def _graph(self, user_id: int, repo: str, updated_at: datetime) -> FlowGraph | None:
        cached = self._graph_cache.get(user_id, repo, updated_at)
        if cached is not None:
            return cached
        detail = await self._repo_maps.get(user_id, repo)
        if detail is None:
            return None
        payload = detail.map.trace.get("flow_graph")
        graph = FlowGraph.model_validate(payload) if payload else None
        if graph is not None:
            self._graph_cache.put(user_id, repo, updated_at, graph)
        return graph

    def _find_entry(self, graph: FlowGraph, entry_id: str) -> FlowNode | None:
        for node in graph.nodes:
            if node.id == entry_id and node.kind == "entry":
                return node
        return None
