from models.decision_candidate import DecisionCandidate
from models.decision_verdict import DecisionVerdict
from services.analysis.site_classifier import SiteClassifier


class HeuristicDecisionJudge:
    def __init__(self, site_classifier: SiteClassifier) -> None:
        self._site_classifier = site_classifier

    def judge(self, candidates: tuple[DecisionCandidate, ...]) -> dict[str, DecisionVerdict]:
        return {candidate.site_id: self._judge_one(candidate) for candidate in candidates}

    def _judge_one(self, candidate: DecisionCandidate) -> DecisionVerdict:
        verdict = self._site_classifier.classify(
            candidate.site, candidate.arm_classes, candidate.arm_reaches
        )
        return DecisionVerdict(verdict=verdict, question="", arm_labels=(), confidence=1.0)
