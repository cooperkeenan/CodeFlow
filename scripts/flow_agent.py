import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "agents" / "render_agent"))
sys.path.insert(0, str(REPO_ROOT / "agents" / "tracer_agent"))

from flow_session import FlowSession
from render_repo import load_dotenv
from screenshot_flow import DEV_PORT, FIXTURE_PATH, FLOW_URL, _build_view, _write_outputs

_USAGE = """usage: flow_agent.py <repo> [--no-llm] [--rebuild] <action> [<action> ...]

actions:
  state                dump visible nodes (id, position, label, +N control)
  overlaps             list overlapping node pairs — empty is the goal
  toggle:<node_id>     click that node's +/- control
  click:<node_id>      click the node body (no-op — FlowCanvas has no onNodeClick)
  isolate:<node_id>    click that node's isolate button
  isolated             dump the isolated (rf-iso) node: box size, canvas fill, border
  dimmed               report dimmed/total nodes and which stayed bright
  key:<name>           press a key, e.g. key:Escape
  press:<text>         click a header button, e.g. press:"collapse all"
  fit                  fit the view
  shot:<path>          screenshot to path
"""


def _print_state(session: FlowSession) -> None:
    state = session.state()
    print(f"header: {state['header']}")
    print(f"visible nodes={len(state['nodes'])} edges={state['edges']}")
    for node in sorted(state["nodes"], key=lambda n: (n["y"] or 0, n["x"] or 0)):
        control = f"  [{node['toggle']}]" if node["toggle"] else ""
        print(f"  ({node['x']:>6},{node['y']:>6})  {node['label'][:44]:<44} {node['id']}{control}")


def _print_isolated(session: FlowSession) -> None:
    info = session.isolated()
    if not info.get("present"):
        print("ISOLATED: absent")
        return
    fill_w = round((info["fillW"] or 0) * 100)
    fill_h = round((info["fillH"] or 0) * 100)
    print(
        f"ISOLATED: {info['id']}  box={info['w']}x{info['h']}  "
        f"canvas={info['canvasW']}x{info['canvasH']}  fill={fill_w}%x{fill_h}%  "
        f"border={info['borderStyle']} {info['borderWidth']} r={info['borderRadius']}"
    )


def _run_action(session: FlowSession, action: str) -> None:
    verb, _, arg = action.partition(":")
    if verb == "state":
        _print_state(session)
    elif verb == "overlaps":
        pairs = session.overlaps()
        print(f"OVERLAPS: {len(pairs)}")
        for a, b in pairs[:20]:
            print(f"  {a}  <->  {b}")
    elif verb == "toggle":
        session.toggle(arg)
        print(f"toggled {arg}")
    elif verb == "click":
        session.click_node(arg)
        print(f"clicked {arg}")
    elif verb == "isolate":
        session.isolate(arg)
        print(f"isolated {arg}")
    elif verb == "isolated":
        _print_isolated(session)
    elif verb == "dimmed":
        info = session.dimmed()
        print(f"DIMMED: {info['dimmed']}/{info['total']}")
        for node_id in info["bright"]:
            print(f"  bright: {node_id}")
    elif verb == "key":
        session.press_key(arg)
        print(f"pressed key {arg}")
    elif verb == "press":
        session.press_button(arg)
        print(f"pressed {arg!r}")
    elif verb == "fit":
        session.fit()
        print("fit view")
    elif verb == "shot":
        path = Path(arg) if arg else REPO_ROOT / "scratch_out" / "flow.png"
        session.shot(path)
        print(f"wrote {path}")
    else:
        print(f"unknown action: {action}")


def main(argv: list[str]) -> int:
    load_dotenv(REPO_ROOT / ".env")
    args = argv[1:]
    if not args:
        print(_USAGE)
        return 1
    no_llm = "--no-llm" in args
    rebuild = "--rebuild" in args
    rest = [a for a in args if a not in ("--no-llm", "--rebuild")]
    target = Path(rest[0]).resolve()
    actions = rest[1:] or ["state"]

    if rebuild or not FIXTURE_PATH.exists():
        graph, view = _build_view(target, no_llm)
        _write_outputs(graph, view, REPO_ROOT / "scratch_out")
        print(f"rebuilt fixture: {len(view.nodes)} placed, {len(view.hidden)} hidden")

    with FlowSession(REPO_ROOT / "frontend", DEV_PORT, FLOW_URL) as session:
        for action in actions:
            _run_action(session, action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
