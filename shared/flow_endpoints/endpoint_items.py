from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointItem:
    id: str
    label: str
    title: str
    one_liner: str
    is_route: bool
    route_count: int
    file: str
    line: int
