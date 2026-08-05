from collections.abc import Mapping

from models.decision_candidate import DecisionCandidate
from models.dispatch_site import DispatchSite
from services.analysis.arm_classifier import ArmClassifier
from services.analysis.component_index import ComponentIndex
from services.analysis.reach_computer import ReachComputer
from services.analysis.site_scorer import SiteScorer

_MAX_SNIPPET_LINES = 25


class DecisionCandidateBuilder:
    def __init__(
        self,
        components: ComponentIndex,
        arm_classifier: ArmClassifier,
        sources: Mapping[str, str],
    ) -> None:
        self._components = components
        self._arm_classifier = arm_classifier
        self._sources = sources

    def build(
        self, site: DispatchSite, reach: ReachComputer, scorer: SiteScorer
    ) -> DecisionCandidate:
        owner_component = self._components.component_of(site.owner)
        reaches = tuple(reach.arm_reach(arm, owner_component) for arm in site.arms)
        classes = tuple(
            self._arm_classifier.classify(arm, r) for arm, r in zip(site.arms, reaches)
        )
        live_union = frozenset().union(
            *(reaches[i] for i, cls in enumerate(classes) if cls == "live")
        )
        heuristic_score = scorer.score(site, live_union)
        return DecisionCandidate(
            site_id=site.id,
            site=site,
            arm_classes=classes,
            arm_reach_sizes=tuple(len(r) for r in reaches),
            arm_reaches=reaches,
            heuristic_score=heuristic_score,
            source_snippet=self._source_snippet(site),
        )

    def _source_snippet(self, site: DispatchSite) -> str:
        text = self._sources.get(site.span.file)
        if text is None:
            return ""
        lines = text.splitlines()
        start = site.span.line
        end = min(site.span.end_line, start + _MAX_SNIPPET_LINES - 1)
        return "\n".join(lines[start - 1 : end])
