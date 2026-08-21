from tour.tour_beat import Beat

MIN_DWELL_MS = 3800
MAX_DWELL_MS = 12000
MS_PER_WORD = 220
MS_PER_BRANCH = 300


def dwell_for(beat: Beat) -> int:
    words = len(beat.body.split())
    branches = len(beat.arms)
    dwell = max(MIN_DWELL_MS, words * MS_PER_WORD + branches * MS_PER_BRANCH)
    return min(dwell, MAX_DWELL_MS)
