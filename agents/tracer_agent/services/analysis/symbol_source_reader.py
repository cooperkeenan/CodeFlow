from collections.abc import Mapping

from shared.models.flow_graph import SourceRef

_MAX_FUNCTION_LINES = 120
_MAX_CLASS_LINES = 40


class SymbolSourceReader:
    def __init__(self, sources: Mapping[str, str]) -> None:
        self._sources = sources

    def read_function(self, span: SourceRef) -> str:
        return self._slice(span, _MAX_FUNCTION_LINES)

    def read_class(self, span: SourceRef) -> str:
        return self._slice(span, _MAX_CLASS_LINES)

    def _slice(self, span: SourceRef, max_lines: int) -> str:
        content = self._sources.get(span.file)
        if content is None:
            return ""
        lines = content.splitlines()
        start = max(span.line - 1, 0)
        end = min(span.end_line, start + max_lines, len(lines))
        if end <= start:
            return ""
        return "\n".join(lines[start:end])
