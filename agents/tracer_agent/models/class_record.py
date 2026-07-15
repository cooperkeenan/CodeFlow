from collections.abc import Mapping
from dataclasses import dataclass

from shared.models.flow_graph import SourceRef


@dataclass(frozen=True)
class ClassRecord:
    fqn: str
    bases: tuple[str, ...]
    methods: tuple[str, ...]
    attr_types: Mapping[str, str]
    span: SourceRef
