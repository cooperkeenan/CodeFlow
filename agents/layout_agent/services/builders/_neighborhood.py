from dataclasses import dataclass

from services.builders._graph_contraction import _ADAPTER, _PRIMARY, ContractionResult, contract
from shared.models.diagram_spec import Component, Edge


def _callee_map(edges: list[Edge]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for e in edges:
        if e.edge_type == "import" or e.source == e.target:
            continue
        if e.source not in result:
            result[e.source] = []
        if e.target not in result[e.source]:
            result[e.source].append(e.target)
    return result


def single_callee_adapters(
    names: set[str],
    all_comps: dict[str, Component],
    edges: list[Edge],
) -> dict[str, str]:
    callees = _callee_map(edges)
    result: dict[str, str] = {}
    for name in names:
        comp = all_comps.get(name)
        if comp is None or comp.role not in _ADAPTER:
            continue
        node_callees = callees.get(name, [])
        if len(node_callees) != 1:
            continue
        callee_name = node_callees[0]
        callee_comp = all_comps.get(callee_name)
        if callee_comp is None or callee_comp.role not in _PRIMARY:
            continue
        result[name] = callee_name
    return result


@dataclass
class ContractedSteps:
    callees: list[str]
    children: list[str]
    folded: dict[str, list[str]]


def contract_steps(
    focus: str,
    callees: list[str],
    children: list[str],
    all_comps: dict[str, Component],
    edges: list[Edge],
) -> ContractedSteps:
    step_set: set[str] = set(callees) | set(children)
    adapters = single_callee_adapters(step_set, all_comps, edges)
    expanded: set[str] = step_set | set(adapters.values())
    intra: list[tuple[str, str]] = [
        (e.source, e.target)
        for e in edges
        if e.edge_type != "import"
        and e.source != e.target
        and e.source in expanded
        and e.target in expanded
    ]
    roles: dict[str, str] = {
        n: all_comps[n].role if n in all_comps else "" for n in expanded
    }
    cr: ContractionResult = contract(expanded, intra, roles)
    fold_map: dict[str, str] = {
        adapter: survivor
        for survivor, adapter_list in cr.folded.items()
        for adapter in adapter_list
    }
    seen_callees: set[str] = set()
    new_callees: list[str] = []
    for name in callees:
        mapped = fold_map.get(name, name)
        if mapped in cr.names and mapped not in seen_callees:
            seen_callees.add(mapped)
            new_callees.append(mapped)

    seen_children: set[str] = set()
    new_children: list[str] = []
    for name in children:
        mapped = fold_map.get(name, name)
        if mapped in cr.names and mapped not in seen_children:
            seen_children.add(mapped)
            new_children.append(mapped)

    return ContractedSteps(new_callees, new_children, cr.folded)


@dataclass
class WrappedFocus:
    folded: list[str]
    pulled_callers: list[str]


def wrapping_adapters(
    focus: str,
    callers: list[str],
    all_comps: dict[str, Component],
    edges: list[Edge],
) -> WrappedFocus:
    callees = _callee_map(edges)
    folded: list[str] = []
    for caller in callers:
        comp = all_comps.get(caller)
        if comp is None or comp.role not in _ADAPTER:
            continue
        caller_callees = callees.get(caller, [])
        if caller_callees == [focus]:
            folded.append(caller)

    wrapper_set: set[str] = set(folded)
    seen: set[str] = set()
    pulled: list[str] = []
    for e in edges:
        if e.edge_type == "import" or e.source == e.target:
            continue
        if e.target in wrapper_set:
            caller_name = e.source
            if caller_name != focus and caller_name not in wrapper_set and caller_name not in seen:
                seen.add(caller_name)
                pulled.append(caller_name)

    return WrappedFocus(folded=folded, pulled_callers=pulled)
