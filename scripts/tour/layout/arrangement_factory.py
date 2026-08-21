from tour.layout.arc_arrangement import ArcArrangement
from tour.layout.arrangement_picker import ArrangementPicker
from tour.layout.fan_arrangement import FanArrangement
from tour.layout.grid_arrangement import GridArrangement
from tour.layout.solo_arrangement import SoloArrangement


def build_arrangement_picker() -> ArrangementPicker:
    solo = SoloArrangement()
    fan = FanArrangement()
    arc = ArcArrangement()
    grid = GridArrangement()
    rules = [
        (lambda beat: len(beat.arms) == 0, solo),
        (lambda beat: len(beat.arms) <= 3, fan),
        (lambda beat: len(beat.arms) <= 5, arc),
        (lambda beat: True, grid),
    ]
    by_name = {"solo": solo, "fan": fan, "arc": arc, "grid": grid}
    return ArrangementPicker(rules, by_name)
