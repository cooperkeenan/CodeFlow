from typing import Callable

from tour.layout.arm_arrangement import ArmArrangement
from tour.tour_beat import Beat

ArrangementPredicate = Callable[[Beat], bool]


class ArrangementPicker:
    def __init__(
        self,
        rules: list[tuple[ArrangementPredicate, ArmArrangement]],
        by_name: dict[str, ArmArrangement],
    ) -> None:
        self._rules = rules
        self._by_name = by_name

    def pick(self, beat: Beat) -> ArmArrangement:
        if beat.arrangement:
            return self._by_name[beat.arrangement]
        for predicate, arrangement in self._rules:
            if predicate(beat):
                return arrangement
        raise KeyError(f"no arrangement matched beat {beat.id!r}")
