from dataclasses import dataclass, field


@dataclass
class EdgeExpectation:
    source_module: str
    target_module: str
    edge_type: str = "http"


@dataclass
class ComponentCountRange:
    module: str
    min: int
    max: int


@dataclass
class AnswerSheet:
    architecture: str
    modules: list[str]
    expected_cross_module_edges: list[EdgeExpectation]
    orchestrators: list[str]
    entry_points: list[str]
    shared_modules: list[str]
    component_count_ranges: list[ComponentCountRange]
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "AnswerSheet":
        return cls(
            architecture=data["architecture"],
            modules=data["modules"],
            expected_cross_module_edges=[
                EdgeExpectation(**e) for e in data.get("expected_cross_module_edges", [])
            ],
            orchestrators=data.get("orchestrators", []),
            entry_points=data.get("entry_points", []),
            shared_modules=data.get("shared_modules", []),
            component_count_ranges=[
                ComponentCountRange(**r) for r in data.get("component_count_ranges", [])
            ],
            notes=data.get("notes", []),
        )
