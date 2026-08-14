from services.symbol_context_resolver import SymbolContextResolver
from services.explanation.heuristic_symbol_explainer import HeuristicSymbolExplainer
from services.step_tree_labeler import StepTreeLabeler
from models.explain_model import ExplainRequest
from models.step_input import StepInput
from models.symbol_slice import SymbolSlice


def make_resolver() -> SymbolContextResolver:
    return SymbolContextResolver(None, None)


def entry_for(fqn: str, functions: dict, classes: dict) -> dict:
    return classes.get(fqn) or functions.get(fqn) or {}


def slice_for(fqn: str, functions: dict, classes: dict) -> SymbolSlice:
    entry = entry_for(fqn, functions, classes)
    kind = "class" if fqn in classes else "function"
    name = entry.get("name", fqn.rsplit(".", 1)[-1])
    return SymbolSlice(fqn=fqn, kind=kind, name=name, signature="", source=entry.get("source", ""))


def node_label(graph: dict, node_id: str) -> str:
    for node in graph.get("nodes", []):
        if node.get("id") == node_id:
            return node.get("label", "")
    return ""


def candidates(nodes_map: dict, functions: dict, classes: dict, resolver: SymbolContextResolver) -> list:
    found = []
    for node_id, fqn in nodes_map.items():
        resolved = resolver.resolve_focus(fqn, functions, classes)
        if resolved is None:
            continue
        primary_kind, primary_fqn, member_fqns = resolved
        symbol_fqns = member_fqns if primary_kind == "class" else [primary_fqn]
        step_count = sum(len(functions.get(f, {}).get("steps", [])) for f in symbol_fqns)
        if step_count > 0:
            found.append((node_id, primary_kind, step_count))
    return sorted(found, key=lambda r: (-r[2], r[0]))


def build_payload(
    node_id: str, graph: dict, symbol_context: dict, resolver: SymbolContextResolver, explainer=None
) -> tuple[dict, dict]:
    functions = symbol_context.get("functions", {})
    classes = symbol_context.get("classes", {})
    focus_fqn = symbol_context["nodes"][node_id]

    resolved = resolver.resolve_focus(focus_fqn, functions, classes)
    if resolved is None:
        raise ValueError(f"node {node_id} resolves to {focus_fqn}, neither a known function nor class")
    primary_kind, primary_fqn, member_fqns = resolved
    helper_fqns = resolver.resolve_helpers(primary_kind, primary_fqn, member_fqns, functions)
    symbol_fqns = member_fqns if primary_kind == "class" else [primary_fqn]

    symbols = [slice_for(f, functions, classes) for f in symbol_fqns]
    helpers = [slice_for(f, functions, classes) for f in helper_fqns]
    sources = {s.fqn: s.source for s in (*symbols, *helpers)}
    steps = resolver.steps_for([*symbol_fqns, *helper_fqns], functions)

    labeler = StepTreeLabeler()
    step_inputs = [StepInput(**s) for s in labeler.flatten(steps)]

    request = ExplainRequest(
        node_id=node_id,
        node_label=node_label(graph, node_id),
        service=resolver.field(primary_fqn, "service", functions, classes),
        module=resolver.field(primary_fqn, "module", functions, classes),
        cls=classes.get(primary_fqn, {}).get("name", "") if primary_kind == "class" else "",
        focus_fqn=primary_fqn,
        symbols=symbols,
        helpers=helpers,
        steps=step_inputs,
    )
    explanation = (explainer or HeuristicSymbolExplainer()).explain(request)
    steps = labeler.apply(steps, explanation.step_labels)

    payload = {
        "explanation": explanation.model_dump(mode="json"),
        "sources": sources,
        "steps": steps,
    }
    summary = {"fqn": primary_fqn, "kind": primary_kind, "methods": len(symbols), "helpers": len(helpers)}
    return payload, summary
