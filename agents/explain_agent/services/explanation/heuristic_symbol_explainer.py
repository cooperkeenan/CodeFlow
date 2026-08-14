import ast
import re

from models.explain_model import ExplainRequest, HelperExplanation, MethodExplanation, NodeExplanation
from models.symbol_slice import SymbolSlice

_SPLIT_PATTERN = re.compile(r"[_\s]+")


class HeuristicSymbolExplainer:
    def explain(self, request: ExplainRequest) -> NodeExplanation:
        primary = self._find(request, request.focus_fqn)
        if primary is not None:
            primary_kind = primary.kind
            primary_name = primary.name
            primary_summary = self._summarize(primary)
        else:
            primary_kind = "class" if request.cls else "function"
            primary_name = request.cls or request.node_label or self._last_segment(request.focus_fqn)
            primary_summary = self._humanize(primary_name)
        methods = [
            MethodExplanation(name=s.name, fqn=s.fqn, summary=self._summarize(s))
            for s in request.symbols
        ]
        helpers = [
            HelperExplanation(name=s.name, fqn=s.fqn, summary=self._summarize(s))
            for s in request.helpers
        ]
        return NodeExplanation(
            node_id=request.node_id,
            focus_fqn=request.focus_fqn,
            service=request.service,
            primary_kind=primary_kind,
            primary_name=primary_name,
            primary_summary=primary_summary,
            methods=methods,
            helpers=helpers,
            step_labels={s.id: s.label for s in request.steps},
            generated=False,
        )

    def _find(self, request: ExplainRequest, fqn: str) -> SymbolSlice | None:
        for symbol in (*request.symbols, *request.helpers):
            if symbol.fqn == fqn:
                return symbol
        return None

    def _last_segment(self, fqn: str) -> str:
        return fqn.rsplit(".", 1)[-1] if fqn else fqn

    def _summarize(self, symbol: SymbolSlice) -> str:
        docstring_summary = self._from_docstring(symbol)
        if docstring_summary:
            return docstring_summary
        return self._humanize(symbol.name)

    def _from_docstring(self, symbol: SymbolSlice) -> str:
        if not symbol.source:
            return ""
        try:
            tree = ast.parse(symbol.source)
        except SyntaxError:
            return ""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    first_sentence = docstring.strip().split(".")[0].strip()
                    return first_sentence
        return ""

    def _humanize(self, name: str) -> str:
        if not name:
            return ""
        words = [w for w in _SPLIT_PATTERN.split(name) if w]
        if not words:
            return name
        sentence = " ".join(words).lower()
        return sentence[0].upper() + sentence[1:]
