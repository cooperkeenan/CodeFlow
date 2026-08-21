from tour.tour_beat import Beat
from tour.tour_chapters import Chapter

CARD_ID_PREFIX = "act:"


def _card_beat(chapter: Chapter, representative: Beat) -> Beat:
    refs = (representative.refs[0],) if representative.refs else ()
    return Beat(
        id=f"{CARD_ID_PREFIX}{chapter.id}",
        kind="step",
        lane=representative.lane,
        label=chapter.title,
        title=chapter.title,
        body=chapter.thesis,
        one_liner=chapter.thesis,
        refs=refs,
        shot="card",
    )


def splice_card_beats(
    groups: list[tuple[str, list[Beat]]], chapters: list[Chapter],
) -> list[tuple[str, list[Beat]]]:
    return [
        (module_name, [_card_beat(chapter, beats[0]), *beats])
        for (module_name, beats), chapter in zip(groups, chapters)
    ]
