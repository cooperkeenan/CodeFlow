from dataclasses import dataclass


@dataclass(frozen=True)
class ParamRecord:
    name: str
    annotation: str | None
