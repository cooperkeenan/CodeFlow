from dataclasses import replace
from itertools import pairwise

from tracer.models.flow_summary import FlowSummary
from tracer.models.index_records import ProjectIndex
from tracer.models.sites import FlowEntry
from tracer.services.analysis.condense.function_summarizer import FunctionSummarizer
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.condense.route_terminal_builder import (
    RouteTerminalBuilder,
)
from tracer.services.analysis.routes.delegation_resolver import DelegationResolver

from shared.models.flow_graph import RouteMember

_Placed = tuple[str | None, str]


class RouteAssembler:
    def __init__(
        self,
        index: ProjectIndex,
        acc: GraphAccumulator,
        summarizer: FunctionSummarizer,
        terminals: RouteTerminalBuilder,
        delegates: DelegationResolver,
    ) -> None:
        self._index = index
        self._acc = acc
        self._summarizer = summarizer
        self._terminals = terminals
        self._delegates = delegates

    def assemble(self, entries: tuple[FlowEntry, ...]) -> tuple[FlowEntry, ...]:
        return tuple(self._assemble_entry(entry) for entry in entries)

    def _assemble_entry(self, entry: FlowEntry) -> FlowEntry:
        handlers = entry.members or (entry.handler_fqn,)
        refs = [self._index.functions[h].span for h in handlers if h in self._index.functions]
        folded = entry.route_count if entry.route_count > 1 else 0
        placed: dict[tuple[str, tuple[str, ...]], _Placed] = {}
        members: list[RouteMember] = []
        for member in entry.route_members:
            key = (member.handler_fqn, tuple(member.wrappers))
            if key not in placed:
                placed[key] = self._place(member)
            first, head = placed[key]
            members.append(member.model_copy(update={"head": head}))
        self._acc.upsert(
            entry.id, "entry", entry.service_root, entry.label,
            refs=refs or None, folded_count=folded, members=members,
        )
        for first, _head in placed.values():
            if first is not None:
                self._acc.connect(entry.id, first, "sequence")
                self._acc.add_container(first, entry.id)
        return replace(entry, routes=tuple(members))

    def _place(self, member: RouteMember) -> _Placed:
        handler = member.handler_fqn
        effective, summary = handler, self._summarizer.summarize(handler)
        if summary.head is None:
            delegate = self._delegates.resolve(handler)
            if delegate is not None:
                effective, summary = delegate, self._summarizer.summarize(delegate)
                if summary.head is not None:
                    self._acc.record_call_boundary(handler, "", delegate)
        summary = self._terminals.terminate(effective, summary)
        if summary.head is None:
            return None, ""
        return self._splice_wrappers(member.wrappers, summary), summary.head

    def _splice_wrappers(self, wrappers: list[str], summary: FlowSummary) -> str:
        assert summary.head is not None
        chain: list[FlowSummary] = []
        for wrapper in wrappers:
            wrapped = self._summarizer.summarize(wrapper)
            if wrapped.head is not None:
                chain.append(wrapped)
        chain.append(summary)
        for current, following in pairwise(chain):
            for tail in current.tails or (current.head,):
                self._acc.connect(tail, following.head, "sequence")
        return chain[0].head
