import json
import sys
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "agents" / "render_agent"))
sys.path.insert(0, str(REPO_ROOT / "agents" / "tracer_agent"))

from browser_driver.flow_reports import print_flowchart, print_isolated, print_state
from browser_driver.flow_session import FlowSession
from render_repo import load_dotenv
from repo_home_fixture import endpoint_slug
from screenshot_flow import DEV_PORT, FIXTURE_PATH, FLOW_URL, _build_view, _write_outputs

HOME_URL = "http://localhost:5173/repo-fixture"
_HOME_SELECTOR = '[data-testid="endpoint-list"]'

_USAGE = """usage: flow_agent.py <repo> [--no-llm] [--rebuild] [--explain <path.json>] <action> [<action> ...]

actions:
  state                dump visible nodes (id, position, label, +N control)
  overlaps             list overlapping node pairs — empty is the goal
  toggle:<node_id>     click that node's +/- control
  click:<node_id>      click the node body (no-op — FlowCanvas has no onNodeClick)
  isolate:<node_id>    click that node's isolate button
  isolated             dump the isolated (rf-iso) node: box size, canvas fill, border
  dimmed               report dimmed/total nodes and which stayed bright
  tap:<testid>         click [data-testid="<testid>"], e.g. tap:view-flow
  flowchart            dump the flowchart view: node/edge counts, overflow, overlaps
  key:<name>           press a key, e.g. key:Escape
  press:<text>         click a header button, e.g. press:"collapse all"
  fit                  fit the view
  shot:<path>          screenshot to path
  endpoint:<entry_id>  click that endpoint link on the repo home page, wait for the diagram

flags:
  --explain <path.json>  stub POST .../explain with this payload and pass ?repo=<name>
  --home                 open the repo home page (endpoint list) instead of the diagram
  --entry <entry_id>     open the diagram for that endpoint instead of the whole repo
"""


def _run_action(session: FlowSession, action: str) -> None:
    verb, _, arg = action.partition(":")
    if verb == "state":
        print_state(session)
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
        print_isolated(session)
    elif verb == "dimmed":
        info = session.dimmed()
        print(f"DIMMED: {info['dimmed']}/{info['total']}")
        for node_id in info["bright"]:
            print(f"  bright: {node_id}")
    elif verb == "endpoint":
        session.open_endpoint(endpoint_slug(arg))
        print(f"opened endpoint {arg}")
    elif verb == "tap":
        session.tap(arg)
        print(f"tapped {arg}")
    elif verb == "pick":
        session.pick_symbol(arg)
        print(f"picked symbol {arg}")
    elif verb == "flowchart":
        print_flowchart(session)
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


def _extract_flag_value(args: list[str], flag: str) -> tuple[str | None, list[str]]:
    if flag not in args:
        return None, args
    index = args.index(flag)
    value = args[index + 1] if index + 1 < len(args) else None
    rest = args[:index] + args[index + 2 :]
    return value, rest


def main(argv: list[str]) -> int:
    load_dotenv(REPO_ROOT / ".env")
    args = argv[1:]
    if not args:
        print(_USAGE)
        return 1
    no_llm = "--no-llm" in args
    rebuild = "--rebuild" in args
    explain_path, args = _extract_flag_value(args, "--explain")
    entry, args = _extract_flag_value(args, "--entry")
    home = "--home" in args
    rest = [a for a in args if a not in ("--no-llm", "--rebuild", "--home")]
    target = Path(rest[0]).resolve()
    actions = rest[1:] or ["state"]

    if rebuild or not FIXTURE_PATH.exists():
        graph, view = _build_view(target, no_llm)
        _write_outputs(graph, view, REPO_ROOT / "scratch_out")
        print(f"rebuilt fixture: {len(view.nodes)} placed, {len(view.hidden)} hidden")

    explain_payload = json.loads(Path(explain_path).read_text()) if explain_path else None
    repo = target.name if explain_payload is not None else None

    url = HOME_URL if home else FLOW_URL
    if entry:
        url = f"{FLOW_URL}?entry={quote(entry, safe='')}"
    selector = _HOME_SELECTOR if home else ".react-flow__node"
    with FlowSession(
        REPO_ROOT / "frontend", DEV_PORT, url, explain_payload, repo, selector
    ) as session:
        for action in actions:
            _run_action(session, action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
