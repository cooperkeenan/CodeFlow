from dataclasses import dataclass


@dataclass
class EvidenceChunk:
    label: str
    evidence: dict
    breadcrumb: str | None = None
