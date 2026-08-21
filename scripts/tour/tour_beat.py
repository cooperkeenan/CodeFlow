from dataclasses import dataclass, field

from shared.models.flow_graph import SourceRef


@dataclass(frozen=True)
class Arm:
    id: str
    label: str
    arm_label: str
    note: str = ""
    kind: str = "outcome"
    terminal: bool = True
    refs: tuple[SourceRef, ...] = ()
    effect_kind: str | None = None
    effect_target: str = ""
    code: str = ""
    code_lang: str = "python"


@dataclass(frozen=True)
class Beat:
    id: str
    kind: str
    lane: str
    label: str
    title: str
    body: str
    one_liner: str = ""
    detail: str = ""
    refs: tuple[SourceRef, ...] = ()
    backing: tuple[str, ...] = ()
    arms: tuple[Arm, ...] = ()
    packets: tuple[str, ...] = ()
    facts: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    shot: str = ""
    arrangement: str = ""

    def converging(self) -> list[Arm]:
        return [arm for arm in self.arms if not arm.terminal]

    def terminal_arms(self) -> list[Arm]:
        return [arm for arm in self.arms if arm.terminal]
