from services.source_slicer import SourceSlicer
from shared.code_store.code_store import CodeStore

_MAX_HELPERS = 12
_MAX_CALLS_PER_CALLER = 20


class SymbolContextResolver:
    def __init__(self, code_store: CodeStore, source_slicer: SourceSlicer) -> None:
        self._code_store = code_store
        self._slicer = source_slicer

    def resolve_focus(
        self, focus_fqn: str, functions: dict, classes: dict
    ) -> tuple[str, str, list[str]] | None:
        if focus_fqn in classes:
            return "class", focus_fqn, sorted(classes[focus_fqn].get("methods", []))
        func = functions.get(focus_fqn)
        if func is None:
            return None
        cls_fqn = func.get("cls", "")
        if cls_fqn and cls_fqn in classes:
            return "class", cls_fqn, sorted(classes[cls_fqn].get("methods", []))
        return "function", focus_fqn, []

    def resolve_helpers(
        self, primary_kind: str, primary_fqn: str, member_fqns: list[str], functions: dict
    ) -> list[str]:
        if primary_kind == "class":
            callees = {c for m in member_fqns for c in functions.get(m, {}).get("callees", [])}
        else:
            callees = set(functions.get(primary_fqn, {}).get("callees", []))
        excluded = set(member_fqns) | {primary_fqn}
        resolved = {c for c in callees if not c.startswith("ext:") and c in functions and c not in excluded}
        return sorted(resolved)[:_MAX_HELPERS]

    async def slice_for(
        self, fqn: str, functions: dict, classes: dict, repo: str, file_cache: dict
    ) -> dict | None:
        if fqn in classes:
            entry, kind = classes[fqn], "class"
        elif fqn in functions:
            entry, kind = functions[fqn], "function"
        else:
            return None
        source = entry.get("source", "")
        if not source:
            span = entry.get("span", {})
            file_path = span.get("file")
            if file_path:
                if file_path not in file_cache:
                    file_cache[file_path] = await self._code_store.get_file(repo, file_path)
                file_row = file_cache[file_path]
                if file_row is not None:
                    source = self._slicer.slice(file_row["content"], span)
        return {
            "fqn": fqn,
            "kind": kind,
            "name": entry.get("name", fqn.rsplit(".", 1)[-1]),
            "signature": "",
            "source": source,
        }

    def field(self, fqn: str, key: str, functions: dict, classes: dict) -> str:
        entry = classes.get(fqn) or functions.get(fqn) or {}
        return entry.get(key, "")

    def sequence_for(
        self, primary_kind: str, primary_fqn: str, member_fqns: list[str], functions: dict
    ) -> list[dict]:
        callers = self._ordered_members(member_fqns, functions) if primary_kind == "class" else [primary_fqn]
        sequence = []
        for caller_fqn in callers:
            entry = functions.get(caller_fqn)
            if entry is None:
                continue
            calls = self._filtered_calls(entry.get("calls", []))
            if primary_kind == "class" and not calls:
                continue
            sequence.append({
                "caller": entry.get("name", caller_fqn.rsplit(".", 1)[-1]),
                "caller_fqn": caller_fqn,
                "calls": calls,
            })
        return sequence

    def _ordered_members(self, member_fqns: list[str], functions: dict) -> list[str]:
        def sort_key(fqn: str) -> tuple[bool, int, str]:
            line = functions.get(fqn, {}).get("span", {}).get("line")
            return (line is None, line or 0, fqn)

        return sorted(member_fqns, key=sort_key)

    def _filtered_calls(self, calls: list[dict]) -> list[dict]:
        filtered = []
        for call in calls:
            fqn = call.get("fqn", "")
            if not fqn or fqn.startswith("ext:"):
                continue
            name = fqn.rsplit(".", 1)[-1]
            if not name:
                continue
            filtered.append({"name": name, "fqn": fqn, "line": call.get("line")})
            if len(filtered) >= _MAX_CALLS_PER_CALLER:
                break
        return filtered
