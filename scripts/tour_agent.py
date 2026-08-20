import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tour_session import TourSession

DEV_PORT = 5173
TOUR_URL = f"http://localhost:{DEV_PORT}/tour"

_USAGE = """usage: tour_agent.py <action> [<action> ...]

actions:
  state           dump visible nodes (id, position, label)
  overlaps        list overlapping node pairs - 0 is the goal
  step:<n>        jump to step n (1-based) and pause
  narration       print the current bubble's counter, title and first body line
  focused         print the node ids currently lit by the tour
  shot:<path>     screenshot to path
"""


def _print_state(session: TourSession) -> None:
    state = session.state()
    print(f"visible nodes={len(state['nodes'])} edges={state['edges']}")
    for node in sorted(state["nodes"], key=lambda n: (n["y"] or 0, n["x"] or 0)):
        print(f"  ({node['x']:>6},{node['y']:>6})  {node['label'][:44]:<44} {node['id']}")


def _run_action(session: TourSession, action: str) -> None:
    if action == "state":
        _print_state(session)
    elif action == "overlaps":
        hits = session.overlaps()
        print(f"overlaps: {len(hits)}")
        for a, b in hits:
            print(f"  {a}  <->  {b}")
    elif action == "narration":
        text = session.narration()
        print(f"  {text['counter']}  {text['title']}")
        print(f"  {text['body'][:120]}")
    elif action == "focused":
        print(f"focused: {session.focused()}")
    elif action.startswith("step:"):
        session.goto_step(int(action.split(":", 1)[1]))
    elif action.startswith("shot:"):
        path = Path(action.split(":", 1)[1])
        session.shot(path if path.is_absolute() else REPO_ROOT / path)
        print(f"wrote {path}")
    else:
        raise SystemExit(f"unknown action {action!r}\n\n{_USAGE}")


def main(argv: list[str]) -> int:
    actions = argv[1:]
    if not actions:
        print(_USAGE)
        return 1
    with TourSession(REPO_ROOT / "frontend", DEV_PORT, TOUR_URL) as session:
        session.pause()
        for action in actions:
            _run_action(session, action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
