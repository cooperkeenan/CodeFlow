from dataclasses import dataclass


@dataclass(frozen=True)
class Trick:
    name: str
    pattern: str
    replacement: str


TRICKS: tuple[Trick, ...] = (
    Trick("x-for-cks", r"c?ks?$", "x"),
    Trick("x-for-ct", r"ct$", "x"),
    Trick("k-for-hard-c", r"c(?![eiy])", "k"),
    Trick("f-for-ph", r"ph", "f"),
    Trick("z-for-s", r"s$", "z"),
    Trick("drop-silent-e", r"e$", ""),
    Trick("r-for-er", r"er$", "r"),
    Trick("y-for-i", r"i(?!$)", "y"),
    Trick("y-for-vowel", r"[aeou](?=[^aeiou]+$)", "y"),
    Trick("kw-for-qu", r"qu", "kw"),
    Trick("t-for-ght", r"ght", "t"),
    Trick("double-tail", r"([bdglmnpt])$", r"\1\1"),
    Trick("drop-double", r"([a-z])\1", r"\1"),
    Trick("u-for-oo", r"oo", "u"),
    Trick("drop-inner-vowel", r"(?<=[a-z])[aeiou](?=[a-z]{2,}$)", ""),
    Trick("v-for-w", r"w$", "v"),
    Trick("shed-final-h", r"h$", ""),
    Trick("q-for-k", r"^k", "q"),
    Trick("ii-for-ee", r"ee", "ii"),
    Trick("drop-final-t", r"(?<=[cs])t$", ""),
)

MIN_TRICK_LENGTH = 3
MAX_TRICK_LENGTH = 9
MAX_TRICKS_PER_WORD = 2
