from flow_session import FlowSession


def print_state(session: FlowSession) -> None:
    state = session.state()
    print(f"header: {state['header']}")
    print(f"visible nodes={len(state['nodes'])} edges={state['edges']}")
    for node in sorted(state["nodes"], key=lambda n: (n["y"] or 0, n["x"] or 0)):
        control = f"  [{node['toggle']}]" if node["toggle"] else ""
        print(f"  ({node['x']:>6},{node['y']:>6})  {node['label'][:44]:<44} {node['id']}{control}")


def print_isolated(session: FlowSession) -> None:
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


def print_flowchart(session: FlowSession) -> None:
    info = session.flowchart()
    if not info.get("present"):
        print(f"FLOWCHART: absent — empty state text: {info.get('emptyText', '')!r}")
        return
    overflow_x = info["scrollWidth"] > info["clientWidth"] + 1
    overflow_y = info["scrollHeight"] > info["clientHeight"] + 1
    print(f"FLOWCHART: nodes={info['nodes']} edges={info['edges']}")
    print(f"  vertical overflow: {overflow_y} (expected/OK, a vertical chart scrolls downward)")
    if overflow_x:
        print("  HORIZONTAL OVERFLOW: True — LAYOUT FAILURE, the chart must not grow sideways")
    else:
        print("  horizontal overflow: False")
    pairs = _overlap_pairs(info["boxes"])
    print(f"  overlapping node-box pairs: {len(pairs)} (must be 0)")
    for a, b in pairs:
        print(f"    {a}  <->  {b}")


def _overlap_pairs(boxes: list[dict]) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if (
                a["x"] < b["x"] + b["w"]
                and b["x"] < a["x"] + a["w"]
                and a["y"] < b["y"] + b["h"]
                and b["y"] < a["y"] + a["h"]
            ):
                found.append((a["id"], b["id"]))
    return sorted(found)
