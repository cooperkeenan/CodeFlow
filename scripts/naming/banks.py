from dataclasses import dataclass

from naming.morphemes import ROOTS, SUFFIXES
from naming.morphemes_optical import OPTICAL_ROOTS, OPTICAL_SUFFIXES
from naming.seed_names import SEED_NAMES
from naming.seed_names_optical import OPTICAL_SEED_NAMES


@dataclass(frozen=True)
class Bank:
    name: str
    seeds: tuple[tuple[str, str], ...]
    roots: tuple[str, ...]
    suffixes: tuple[str, ...]


BANKS: dict[str, Bank] = {
    "craft": Bank("craft", SEED_NAMES, ROOTS, SUFFIXES),
    "optical": Bank("optical", OPTICAL_SEED_NAMES, OPTICAL_ROOTS, OPTICAL_SUFFIXES),
}

DEFAULT_BANK = "craft"
