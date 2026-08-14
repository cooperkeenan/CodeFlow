from models.call_site import CallSite


class CallFqnLookup:
    def __init__(self, callsites: tuple[CallSite, ...]) -> None:
        by_key: dict[tuple[str, int, str], str] = {}
        for site in callsites:
            if not site.targets:
                continue
            fqn = site.targets[0].fqn
            key = (site.caller, site.line, site.call_source)
            existing = by_key.get(key)
            if existing is None or fqn < existing:
                by_key[key] = fqn
        self._by_key = by_key

    def fqn_for(self, caller: str, line: int, call_source: str) -> str:
        return self._by_key.get((caller, line, call_source), "")
