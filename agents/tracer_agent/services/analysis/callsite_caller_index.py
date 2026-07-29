from collections import defaultdict

from models.call_site import CallSite


class CallSiteCallerIndex:
    def __init__(self, callsites: tuple[CallSite, ...]) -> None:
        self._by_caller: dict[str, list[CallSite]] = defaultdict(list)
        for site in callsites:
            self._by_caller[site.caller].append(site)

    def callsites_for(self, caller_fqn: str) -> tuple[CallSite, ...]:
        return tuple(self._by_caller.get(caller_fqn, ()))
