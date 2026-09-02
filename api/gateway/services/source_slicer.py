class SourceSlicer:
    def __init__(self, max_lines: int = 120):
        self._max_lines = max_lines

    def slice(self, content: str, ref: dict) -> str:
        lines = content.splitlines()
        start = max(ref.get("line", 1) - 1, 0)
        end_line = ref.get("end_line", start + 1)
        end = min(end_line, start + self._max_lines, len(lines))
        if start >= len(lines) or start >= end:
            return ""
        return "\n".join(lines[start:end])
