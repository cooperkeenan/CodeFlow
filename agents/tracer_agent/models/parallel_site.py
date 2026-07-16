from dataclasses import dataclass

from shared.models.flow_graph import SourceRef


@dataclass(frozen=True)
class ParallelSite:
    id: str
    owner: str
    line: int
    callees: tuple[str, ...]
    span: SourceRef
