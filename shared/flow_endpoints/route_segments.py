_PARAM_CHARS = frozenset("<{(\\[]*+?|.^$)}>")


def literal_segments(path: str) -> tuple[str, ...]:
    trimmed = path.removeprefix("^").removesuffix("$")
    parts = [p for p in trimmed.split("/") if p]
    return tuple(p for p in parts if not _PARAM_CHARS.intersection(p))
