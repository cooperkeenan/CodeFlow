from dataclasses import dataclass


@dataclass(frozen=True)
class FlowEntry:
    id: str
    handler_fqn: str
    label: str
    service_root: str
    method: str = ""
    path: str = ""
