def is_placeholder(segment: str) -> bool:
    return segment.startswith("{") and segment.endswith("}")


def split_segments(path: str) -> tuple[str, ...]:
    return tuple(part for part in path.split("/") if part)


def normalize_out_path(target: str) -> tuple[str, ...] | None:
    if not target or "://" in target:
        return None
    if not target.startswith("/"):
        return None
    return split_segments(target)
