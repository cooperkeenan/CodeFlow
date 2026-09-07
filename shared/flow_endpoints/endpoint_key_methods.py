from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.models.flow_graph import FlowGraph

_MAX_KEY_METHODS = 12


class KeyMethodSelector:
    def __init__(self, subgraph: EndpointSubgraph | None = None) -> None:
        self._subgraph = subgraph or EndpointSubgraph()

    def select(self, graph: FlowGraph, entry_id: str, symbol_context: dict) -> list[str]:
        functions = symbol_context.get("functions", {})
        classes = symbol_context.get("classes", {})
        handler_fqn = symbol_context.get("nodes", {}).get(entry_id)
        if handler_fqn is not None:
            return self._select_from_handler(handler_fqn, functions, classes)
        return self._select_from_fallback(graph, entry_id, functions, classes)

    def _select_from_handler(
        self, handler_fqn: str, functions: dict, classes: dict
    ) -> list[str]:
        primary_fqn, key_base = self._resolve_focus(handler_fqn, functions, classes)
        if primary_fqn is None:
            return []
        callees = self._callees_for(primary_fqn, key_base, functions)
        excluded = set(key_base) | {primary_fqn}
        helper_fqns = {
            c for c in callees if not c.startswith("ext:") and c not in excluded and (c in functions or c in classes)
        }
        rest = sorted((set(key_base) | helper_fqns) - {primary_fqn})
        ordered = [primary_fqn] + [fqn for fqn in rest if fqn != primary_fqn]
        return ordered[:_MAX_KEY_METHODS]

    def _resolve_focus(
        self, focus_fqn: str, functions: dict, classes: dict
    ) -> tuple[str | None, list[str]]:
        if focus_fqn in classes:
            return focus_fqn, sorted(classes[focus_fqn].get("methods", []))
        func = functions.get(focus_fqn)
        if func is None:
            return None, []
        cls_fqn = func.get("cls", "")
        if cls_fqn and cls_fqn in classes:
            return cls_fqn, sorted(classes[cls_fqn].get("methods", []))
        return focus_fqn, []

    def _callees_for(self, primary_fqn: str, key_base: list[str], functions: dict) -> set[str]:
        if key_base:
            return {c for m in key_base for c in functions.get(m, {}).get("callees", [])}
        return set(functions.get(primary_fqn, {}).get("callees", []))

    def _select_from_fallback(
        self, graph: FlowGraph, entry_id: str, functions: dict, classes: dict
    ) -> list[str]:
        sliced = self._subgraph.slice(graph, entry_id)
        if sliced is None:
            return []
        owners = sorted({node.owner_fqn for node in sliced.nodes if node.owner_fqn})
        valid = [fqn for fqn in owners if fqn in functions or fqn in classes]
        return valid[:_MAX_KEY_METHODS]
