def overlap_pairs(boxes: list[dict]) -> list[tuple[str, str]]:
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
