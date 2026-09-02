import math

from tracer.models.call_records import CallSite
from tracer.services.analysis.config import SignificanceConfig
from tracer.services.analysis.resolve.indexes import ComponentIndex


class UtilityDamper:
    def __init__(self, components: ComponentIndex, config: SignificanceConfig) -> None:
        self._components = components
        self._config = config

    def compute(self, callsites: tuple[CallSite, ...]) -> frozenset[str]:
        callers: dict[str, set[str]] = {}
        for site in callsites:
            source = self._components.component_of(site.caller)
            if source is None:
                continue
            for target in site.targets:
                dest = self._components.component_of(target.fqn)
                if dest is None or dest == source:
                    continue
                callers.setdefault(dest, set()).add(site.caller)
        fan_in = {component: len(sources) for component, sources in callers.items()}
        threshold = self._threshold(tuple(fan_in.values()))
        return frozenset(c for c, count in fan_in.items() if count >= threshold)

    def _threshold(self, counts: tuple[int, ...]) -> int:
        if not counts:
            return self._config.utility_min_fan_in
        ordered = sorted(counts)
        rank = math.ceil(self._config.utility_percentile * len(ordered)) - 1
        p90 = ordered[max(0, rank)]
        return max(self._config.utility_min_fan_in, p90)
