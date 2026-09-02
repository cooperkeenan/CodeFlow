import difflib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "agents" / "render_agent"))
sys.path.insert(0, str(REPO_ROOT / "agents" / "tracer_agent"))

from render_repo import load_dotenv, read_python_sources
from screenshot_flow import _build_view

sys.path.insert(0, str(REPO_ROOT / "api"))
sys.path.insert(0, str(REPO_ROOT / "agents" / "explain_agent"))

from symbol_explain_builder import build_payload, candidates, make_resolver

_USAGE = """usage: dump_explain.py <repo_or_out_dir> <node_id> [out.json]
       dump_explain.py <repo_or_out_dir> --list
"""


def _load_graph(target: Path, no_llm: bool) -> dict:
    if target.is_dir():
        graph_path = target / "flow_graph.json"
        return json.loads(graph_path.read_text())
    files = read_python_sources(target)
    print(f"Indexed {len(files)} Python files from {target}")
    graph, _view = _build_view(target, no_llm)
    return json.loads(graph.model_dump_json())


def _print_candidates(nodes_map: dict, functions: dict, classes: dict, resolver) -> None:
    rows = candidates(nodes_map, functions, classes, resolver)
    print(f"{len(rows)} candidate node ids with steps:")
    for node_id, kind, step_count in rows:
        print(f"  steps={step_count:<4} kind={kind:<8} {node_id}")


def _print_summary(node_id: str, payload: dict, summary: dict) -> None:
    print(f"node_id={node_id} fqn={summary['fqn']} kind={summary['kind']}")
    print(f"methods={summary['methods']} helpers={summary['helpers']}")
    for fqn in sorted(payload["steps"]):
        print(f"  steps[{fqn}] = {len(payload['steps'][fqn])}")


def _explainer(use_llm: bool):
    if not use_llm:
        return None
    from explain.core.config import get_settings
    from explain.services.explanation.symbol_explainer_factory import build_symbol_explainer

    key = get_settings().ANTHROPIC_API_KEY
    if not key:
        raise SystemExit("--llm needs ANTHROPIC_API_KEY in Settings (.env)")
    return build_symbol_explainer(key)


def main(argv: list[str]) -> int:
    load_dotenv(REPO_ROOT / ".env")
    args = argv[1:]
    if not args:
        print(_USAGE)
        return 1
    no_llm = "--no-llm" in args
    list_mode = "--list" in args
    use_llm = "--llm" in args
    rest = [a for a in args if a not in ("--no-llm", "--list", "--llm")]
    if not rest:
        print(_USAGE)
        return 1

    target = Path(rest[0]).resolve()
    graph = _load_graph(target, no_llm)
    symbol_context = graph.get("meta", {}).get("symbol_context")
    if symbol_context is None:
        print("no symbol_context on this flow_graph — re-run the analysis to get one")
        return 1
    nodes_map = symbol_context.get("nodes", {})
    functions = symbol_context.get("functions", {})
    classes = symbol_context.get("classes", {})
    resolver = make_resolver()

    if list_mode:
        _print_candidates(nodes_map, functions, classes, resolver)
        return 0

    if len(rest) < 2:
        print(_USAGE)
        return 1
    node_id = rest[1]
    out_path = Path(rest[2]) if len(rest) > 2 else REPO_ROOT / "scratch_out" / "explain.json"

    if node_id not in nodes_map:
        print(f"unknown node id: {node_id}")
        for guess in difflib.get_close_matches(node_id, nodes_map.keys(), n=10, cutoff=0.0):
            print(f"  close match: {guess}")
        return 1

    try:
        payload, summary = build_payload(node_id, graph, symbol_context, resolver, _explainer(use_llm))
    except ValueError as error:
        print(str(error))
        return 1

    _print_summary(node_id, payload, summary)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
