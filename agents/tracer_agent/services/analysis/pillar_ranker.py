from models.call_site import CallSite
from models.pillar_scores import PillarScores
from services.analysis.component_index import ComponentIndex
from services.analysis.hits_iteration import run_hits
from services.analysis.significance_config import SignificanceConfig


class PillarRanker:
    def __init__(self, components: ComponentIndex, config: SignificanceConfig) -> None:
        self._components = components
        self._config = config

    def rank(self, callsites: tuple[CallSite, ...]) -> PillarScores:
        adjacency: dict[str, dict[str, int]] = {}
        nodes: set[str] = set()
        for site in callsites:
            source = self._components.component_of(site.caller)
            if source is None:
                continue
            for target in site.targets:
                dest = self._components.component_of(target.fqn)
                if dest is None or dest == source:
                    continue
                nodes.add(source)
                nodes.add(dest)
                bucket = adjacency.setdefault(dest, {})
                bucket[source] = bucket.get(source, 0) + 1
        hub, authority = run_hits(
            adjacency,
            frozenset(nodes),
            self._config.pillar_hits_iterations,
            self._config.pillar_score_decimals,
        )
        return PillarScores(hub, authority)
