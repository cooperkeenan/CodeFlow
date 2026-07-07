import re

from services.assembly.graph_validator import ValidationResult


class CorrectionPromptBuilder:
    def build(self, result: ValidationResult, attempt: int) -> str | None:
        if not result.correctable_warnings:
            return None
        sections = [
            f"Your diagram has the following issues that must be corrected.\n"
            f"This is correction attempt {attempt} of 3."
        ]
        missing = self._parse_w5(result.correctable_warnings)
        orphaned = self._parse_w1(result.correctable_warnings)
        confirmed = self._parse_w2(result.correctable_warnings)
        if missing:
            lines = "\n".join(f"{p} -> {c} (edge_type: call)" for p, c in missing)
            sections.append(
                "MISSING EDGES — add these to your edges list:\n"
                "These components appear in a parent's children list but have no incoming edge from "
                "that parent. Every child relationship must have a corresponding edge.\n\n" + lines
            )
        if orphaned:
            sections.append(
                "ORPHANED COMPONENTS — these components have no edges at all:\n"
                "Add at least one incoming or outgoing edge, or remove the component if it is not needed.\n\n"
                + "\n".join(orphaned)
            )
        if confirmed:
            lines = "\n".join(f"{f} -> {t} (edge_type: call)" for f, t in confirmed)
            sections.append(
                "CONFIRMED EDGES FROM EVIDENCE — these edges are verified by both import and call "
                "analysis but are missing from your output. Add them:\n\n" + lines
            )
        sections.append(
            "Return the complete corrected JSON matching the original schema exactly.\n"
            "Do not change anything that is not listed above.\n"
            "Do not add new components.\n"
            "Do not remove existing components."
        )
        return "\n\n".join(sections)

    def _parse_w5(self, warnings: list[str]) -> list[tuple[str, str]]:
        result = []
        for w in warnings:
            m = re.match(r"W5: (\S+) lists (\S+) as child", w)
            if m:
                result.append((m.group(1), m.group(2)))
        return result

    def _parse_w1(self, warnings: list[str]) -> list[str]:
        result = []
        for w in warnings:
            m = re.match(r"W1: (\S+) has no incoming", w)
            if m:
                result.append(m.group(1))
        return result

    def _parse_w2(self, warnings: list[str]) -> list[tuple[str, str]]:
        result = []
        for w in warnings:
            m = re.match(r"W2: confirmed_edge (\S+) -> (\S+) missing", w)
            if m:
                result.append((m.group(1), m.group(2)))
        return result
