from dataclasses import dataclass


@dataclass(frozen=True)
class NodeNaming:
    label: str
    one_liner: str
