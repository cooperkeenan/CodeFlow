from dataclasses import dataclass

from models.class_record import ClassRecord


@dataclass(frozen=True)
class ClassAnalysis:
    record: ClassRecord
    is_abstract: bool
    is_protocol: bool
    method_names: frozenset[str]
