from tour.tour_shot_validation_error import ShotValidationError
from tour.tour_shots import SHOT_NAMES

SHOT_W = 1900
SHOT_H = 900


def _check_shot_names(steps: list[dict]) -> None:
    for step in steps:
        if step["shot"] not in SHOT_NAMES:
            raise ShotValidationError(f"step {step['id']} has unknown shot {step['shot']!r}")


def _positions(view: dict, geometry: dict) -> dict[str, tuple[int, int, int, int]]:
    out: dict[str, tuple[int, int, int, int]] = {}
    for item in view["nodes"]:
        size = geometry[item["shape"]]
        pos = item["position"]
        out[item["id"]] = (pos["x"], pos["y"], size["width"], size["height"])
    return out


def _span(step: dict, positions: dict[str, tuple[int, int, int, int]]) -> tuple[int, int]:
    left = [positions[node_id][0] for node_id in step["focus"]]
    top = [positions[node_id][1] for node_id in step["focus"]]
    right = [positions[node_id][0] + positions[node_id][2] for node_id in step["focus"]]
    bottom = [positions[node_id][1] + positions[node_id][3] for node_id in step["focus"]]
    return max(right) - min(left), max(bottom) - min(top)


def _check_shot_bounds(steps: list[dict], positions: dict[str, tuple[int, int, int, int]]) -> None:
    for step in steps:
        width, height = _span(step, positions)
        if width > SHOT_W or height > SHOT_H:
            raise ShotValidationError(
                f"step {step['id']} focus spans {width}x{height}px, "
                f"budget is {SHOT_W}x{SHOT_H}px"
            )


def validate_shots(view: dict, steps: list[dict], geometry: dict) -> None:
    _check_shot_names(steps)
    positions = _positions(view, geometry)
    _check_shot_bounds(steps, positions)
