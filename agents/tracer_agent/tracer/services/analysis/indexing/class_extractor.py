import ast

from tracer.models.index_records import ClassRecord
from tracer.services.analysis.indexing.annotation_resolver import AnnotationResolver
from tracer.services.analysis.indexing.attr_type_collector import AttrTypeCollector
from tracer.services.analysis.syntax.types import ClassAnalysis

from shared.models.flow_graph import SourceRef


class ClassExtractor:
    def __init__(self, attr_type_collector: AttrTypeCollector) -> None:
        self._attr_type_collector = attr_type_collector

    def extract(
        self, node: ast.ClassDef, module_fqn: str, resolver: AnnotationResolver, relpath: str
    ) -> ClassAnalysis:
        fqn = f"{module_fqn}.{node.name}"
        bases = tuple(resolver.resolve(base) or "" for base in node.bases)
        method_defs = [item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
        record = ClassRecord(
            fqn=fqn,
            bases=bases,
            methods=tuple(sorted(f"{fqn}.{item.name}" for item in method_defs)),
            attr_types=self._attr_type_collector.collect(node, resolver),
            span=SourceRef(file=relpath, line=node.lineno, end_line=node.end_lineno or node.lineno),
        )
        is_protocol = self._is_protocol(node)
        is_abstract = is_protocol or self._is_abc(node) or self._has_abstractmethod(method_defs)
        method_names = frozenset(item.name for item in method_defs)
        return ClassAnalysis(record=record, is_abstract=is_abstract, is_protocol=is_protocol, method_names=method_names)

    def _is_protocol(self, node: ast.ClassDef) -> bool:
        return any(self._base_name(base) == "Protocol" for base in node.bases)

    def _is_abc(self, node: ast.ClassDef) -> bool:
        if any(self._base_name(base) in {"ABC", "ABCMeta"} for base in node.bases):
            return True
        return any(kw.arg == "metaclass" and self._base_name(kw.value) == "ABCMeta" for kw in node.keywords)

    def _has_abstractmethod(self, method_defs: list[ast.FunctionDef | ast.AsyncFunctionDef]) -> bool:
        return any(
            self._base_name(dec) == "abstractmethod" for item in method_defs for dec in item.decorator_list
        )

    def _base_name(self, node: ast.expr) -> str:
        return ast.unparse(node).rsplit(".", 1)[-1].split("[")[0]
