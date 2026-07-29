from typing import Protocol

from models.decision_candidate import DecisionCandidate
from models.decision_verdict import DecisionVerdict


class DecisionJudge(Protocol):
    def judge(self, candidates: tuple[DecisionCandidate, ...]) -> dict[str, DecisionVerdict]: ...
