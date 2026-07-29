from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleRecord:
    fqn: str
    bindings: Mapping[str, str]
    classes: tuple[str, ...]
    functions: tuple[str, ...]
