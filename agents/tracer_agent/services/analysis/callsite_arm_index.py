from collections import defaultdict

from models.call_site import CallSite


class CallSiteArmIndex:
    def __init__(self, callsites: tuple[CallSite, ...]) -> None:
        self._by_arm: dict[tuple[str, int], list[CallSite]] = defaultdict(list)
        for site in callsites:
            for frame in site.context:
                self._by_arm[(frame.site_id, frame.arm_index)].append(site)

    def callsites_for(self, site_id: str, arm_index: int) -> tuple[CallSite, ...]:
        return tuple(self._by_arm.get((site_id, arm_index), ()))
