import math

from models.dispatch_site import DispatchSite
from models.project_index import ProjectIndex
from services.analysis.route_reach_index import RouteReachIndex
from services.analysis.significance_config import SignificanceConfig

_KIND_BONUS = frozenset({"route", "table", "polymorphic"})


class SiteScorer:
    def __init__(
        self, config: SignificanceConfig, index: ProjectIndex, route_reach: RouteReachIndex
    ) -> None:
        self._config = config
        self._index = index
        self._route_reach = route_reach

    def score(self, site: DispatchSite, live_union: frozenset[str]) -> float:
        reach_term = self._config.weight_reach * math.log2(1 + len(live_union))
        provenance_term = self._config.weight_provenance * self._provenance(site)
        terminal_term = self._config.weight_terminal * (0.0 if site.reconverges else 1.0)
        kind_term = self._config.weight_dispatch_kind * (1.0 if site.kind in _KIND_BONUS else 0.0)
        return reach_term + provenance_term + terminal_term + kind_term

    def _provenance(self, site: DispatchSite) -> int:
        owner = self._index.functions.get(site.owner)
        if owner is None:
            return 0
        params = {param.name for param in owner.params}
        if not any(read in params for read in site.selector_reads):
            return 0
        return 2 if self._route_reach.is_route_reachable(site.owner) else 1
