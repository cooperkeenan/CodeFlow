STAGE_LABELS: dict[str, str] = {
    "fetch": "Fetch sources",
    "read": "Read files",
    "index": "Index",
    "resolve": "Resolve calls",
    "forks": "Find forks",
    "effects": "Detect effects",
    "judge": "Judge decisions",
    "condense": "Condense",
    "entries": "Find entries",
    "stitch": "Stitch",
    "rank": "Rank",
    "budget": "Budget",
    "name": "Label",
    "review": "Review",
    "symbols": "Symbols",
}

STAGE_NAMES: list[str] = list(STAGE_LABELS)


def label_for(name: str) -> str:
    return STAGE_LABELS.get(name, name)
