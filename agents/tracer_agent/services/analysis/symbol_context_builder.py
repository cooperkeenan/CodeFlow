from models.call_site import CallSite
from models.project_index import ProjectIndex
from shared.models.flow_graph import FlowGraph, FlowNode

from services.analysis.call_fqn_lookup import CallFqnLookup
from services.analysis.callee_index import CalleeIndex
from services.analysis.function_step_visitor import FunctionStepVisitor
from services.analysis.service_root_resolver import ServiceRootResolver
from services.analysis.symbol_source_reader import SymbolSourceReader

_SEED_PREFIX = "entry:seed:"


class SymbolContextBuilder:
    def __init__(
        self,
        index: ProjectIndex,
        callsites: tuple[CallSite, ...],
        roots: ServiceRootResolver,
        source_reader: SymbolSourceReader | None = None,
    ) -> None:
        self._index = index
        self._callees = CalleeIndex(callsites)
        self._call_fqn_lookup = CallFqnLookup(callsites)
        self._roots = roots
        self._sources = source_reader
        self._by_def: dict[tuple[str, int], str] = {}
        for fqn in sorted(index.functions):
            span = index.functions[fqn].span
            self._by_def.setdefault((span.file, span.line), fqn)

    def build(self, graph: FlowGraph) -> dict:
        owners = {node.id: self._owner_of(node) for node in graph.nodes}
        seeds = {fqn for fqn in owners.values() if fqn}
        for node in graph.nodes:
            seeds.update(node.backing)
        function_scope, class_scope = self._expand(seeds)
        return {
            "nodes": {node_id: fqn for node_id, fqn in sorted(owners.items()) if fqn},
            "functions": {fqn: self._function_entry(fqn) for fqn in sorted(function_scope)},
            "classes": {fqn: self._class_entry(fqn) for fqn in sorted(class_scope)},
        }

    def _owner_of(self, node: FlowNode) -> str:
        if node.owner_fqn:
            return node.owner_fqn
        for ref in node.refs:
            fqn = self._by_def.get((ref.file, ref.line))
            if fqn is not None:
                return fqn
        if node.backing:
            return node.backing[0]
        if node.id.startswith(_SEED_PREFIX):
            component = node.id[len(_SEED_PREFIX):]
            if component in self._index.classes or component in self._index.functions:
                return component
        return ""

    def _expand(self, seeds: set[str]) -> tuple[set[str], set[str]]:
        function_scope = {fqn for fqn in seeds if fqn in self._index.functions}
        class_scope = {fqn for fqn in seeds if fqn in self._index.classes}
        for fqn in sorted(function_scope):
            record = self._index.functions[fqn]
            if record.cls:
                class_scope.add(record.cls)
            for callee in self._callees.callees_of(fqn):
                if callee in self._index.functions:
                    function_scope.add(callee)
        for cls_fqn in sorted(class_scope):
            cls_record = self._index.classes.get(cls_fqn)
            if cls_record is None:
                continue
            for method in cls_record.methods:
                if method in self._index.functions:
                    function_scope.add(method)
        return function_scope, class_scope

    def _function_entry(self, fqn: str) -> dict:
        record = self._index.functions[fqn]
        visitor = FunctionStepVisitor(fqn, self._call_fqn_lookup)
        entry = {
            "name": record.name,
            "module": record.module,
            "cls": record.cls or "",
            "service": self._roots.root_of(fqn),
            "is_async": record.is_async,
            "span": record.span.model_dump(),
            "callees": list(self._callees.callees_of(fqn)),
            "steps": visitor.build(record.body.body),
        }
        if self._sources is not None:
            entry["source"] = self._sources.read_function(record.span)
        return entry

    def _class_entry(self, fqn: str) -> dict:
        record = self._index.classes[fqn]
        entry = {
            "name": fqn.rsplit(".", 1)[-1],
            "module": fqn.rsplit(".", 1)[0],
            "service": self._roots.root_of(fqn),
            "bases": sorted(record.bases),
            "methods": sorted(record.methods),
            "span": record.span.model_dump(),
        }
        if self._sources is not None:
            entry["source"] = self._sources.read_class(record.span)
        return entry
