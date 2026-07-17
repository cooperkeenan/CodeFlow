from dataclasses import dataclass, field


@dataclass(frozen=True)
class FlowEntry:
    id: str
    handler_fqn: str
    label: str
    service_root: str
    method: str = ""
    path: str = ""
    members: tuple[str, ...] = field(default_factory=tuple)
    route_count: int = 1
