from models.call_site import CallSite


class CalleeIndex:
    def __init__(self, callsites: tuple[CallSite, ...]) -> None:
        self._by_caller: dict[str, set[str]] = {}
        for site in callsites:
            bucket = self._by_caller.setdefault(site.caller, set())
            for target in site.targets:
                bucket.add(target.fqn)

    def callees_of(self, fqn: str) -> tuple[str, ...]:
        return tuple(sorted(self._by_caller.get(fqn, ())))
