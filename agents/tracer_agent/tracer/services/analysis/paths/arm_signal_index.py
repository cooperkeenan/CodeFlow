from collections.abc import Iterable

from tracer.models.call_records import Arm
from tracer.models.sites import DispatchSite


class ArmSignalIndex:
    def __init__(self, sites: Iterable[DispatchSite]) -> None:
        self._arms: dict[tuple[str, int], Arm] = {
            (site.id, arm.index): arm for site in sites for arm in site.arms
        }

    def arm(self, site_id: str, arm_index: int) -> Arm | None:
        return self._arms.get((site_id, arm_index))
