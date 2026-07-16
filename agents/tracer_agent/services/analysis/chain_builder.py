from shared.models.flow_graph import Badge, EdgeKind, SourceRef

from services.analysis.graph_accumulator import GraphAccumulator
from services.analysis.label_synthesizer import LabelSynthesizer


class ChainBuilder:
    def __init__(
        self, acc: GraphAccumulator, labels: LabelSynthesizer, owner: str, lane: str
    ) -> None:
        self._acc = acc
        self._labels = labels
        self._owner = owner
        self.lane = lane
        self.head: str | None = None
        self.frontier: list[str] = []
        self._backing: list[str] = []
        self._refs: list[SourceRef] = []
        self._badges: set[Badge] = set()
        self._first_fqn: str | None = None
        self._first_line: int = 0

    def add_backing(self, fqn: str, ref: SourceRef | None, badges: set[Badge]) -> None:
        if self._first_fqn is None:
            self._first_fqn = fqn
            self._first_line = ref.line if ref is not None else 0
        if fqn not in self._backing:
            self._backing.append(fqn)
        if ref is not None:
            self._refs.append(ref)
        self._badges.update(badges)

    def flush(self) -> None:
        if self._first_fqn is None:
            return
        node_id = f"step:{self._owner}:{self._first_line}"
        self._acc.upsert(
            node_id, "step", self.lane, self._labels.step_label(self._backing),
            backing=list(self._backing), refs=list(self._refs), badges=set(self._badges),
        )
        self._link(node_id, "sequence", "", "")
        self._reset()

    def attach(self, node_id: str, kind: EdgeKind = "sequence", arm_label: str = "", group_id: str = "") -> None:
        self.flush()
        self._link(node_id, kind, arm_label, group_id)

    def splice(self, head: str | None, tails: tuple[str, ...], badges: set[Badge]) -> None:
        self.flush()
        if head is None:
            return
        for badge in badges:
            self._acc.add_badge(head, badge)
        self._link(head, "sequence", "", "", advance=False)
        self.frontier = list(tails) if tails else [head]

    def fan_out(self, node_id: str, tails: list[str]) -> None:
        self.frontier = tails or [node_id]

    def _link(
        self, node_id: str, kind: EdgeKind, arm_label: str, group_id: str, advance: bool = True
    ) -> None:
        if self.head is None:
            self.head = node_id
        for src in self.frontier:
            self._acc.connect(src, node_id, kind, arm_label, group_id)
        if advance:
            self.frontier = [node_id]

    def _reset(self) -> None:
        self._backing = []
        self._refs = []
        self._badges = set()
        self._first_fqn = None
        self._first_line = 0
