from tour.tour_beat import Beat

SHOT_NAMES = ("detail", "medium", "wide", "establish", "card")


def default_shot(beat: Beat) -> str:
    arm_count = len(beat.arms)
    if arm_count == 0:
        return "detail"
    if arm_count <= 5:
        return "medium"
    return "wide"
