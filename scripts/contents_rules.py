from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

MAX_FLOWS = 80
MAX_STEPS = 12
MAX_DEPTH = 4
MAX_EXTERNALS = 10
MODULE_SUFFIX = ".<module>"


@dataclass
class CallGraph:
    functions: dict[str, Any]
    callees: dict[str, set[str]]
    indegree: dict[str, int]
    externals: dict[str, set[str]]

    @classmethod
    def build(cls, functions: dict[str, Any], sites: Any) -> CallGraph:
        callees: dict[str, set[str]] = defaultdict(set)
        indegree: dict[str, int] = defaultdict(int)
        externals: dict[str, set[str]] = defaultdict(set)
        for site in sites:
            for target in site.targets:
                if target.fqn.startswith("ext:"):
                    module = external_module(target.fqn)
                    if module != "builtins":
                        externals[site.caller].add(module)
                elif target.fqn in functions and site.caller in functions:
                    if is_call(site.caller) and target.fqn not in callees[site.caller]:
                        indegree[target.fqn] += 1
                    callees[site.caller].add(target.fqn)
        return cls(functions, callees, indegree, externals)

    def sort_key(self, fqn: str) -> tuple[str, int, str]:
        span = self.functions[fqn].span
        return (span.file, span.line, fqn)

    def closure(self, root: str) -> set[str]:
        seen: set[str] = set()
        stack = [root]
        while stack:
            for callee in self.callees.get(stack.pop(), ()):
                if callee not in seen and callee != root:
                    seen.add(callee)
                    stack.append(callee)
        return seen

    def steps(self, root: str) -> list[dict[str, Any]]:
        visited = {root}
        out: list[dict[str, Any]] = []
        frontier = [root]
        depth = 0
        while frontier and depth < MAX_DEPTH and len(out) < MAX_STEPS:
            depth += 1
            next_frontier: list[str] = []
            for fqn in frontier:
                for child in sorted(self.callees.get(fqn, ()), key=self.sort_key):
                    if child in visited or len(out) >= MAX_STEPS:
                        continue
                    visited.add(child)
                    out.append(symbol(child, self.functions[child], depth=depth))
                    next_frontier.append(child)
            frontier = next_frontier
        return out

    def ordered(self, root: str) -> list[str]:
        visited = {root}
        order = [root]
        frontier = [root]
        while frontier:
            next_frontier: list[str] = []
            for fqn in frontier:
                for child in sorted(self.callees.get(fqn, ()), key=self.sort_key):
                    if child not in visited:
                        visited.add(child)
                        order.append(child)
                        next_frontier.append(child)
            frontier = next_frontier
        return order

    def is_root(self, fqn: str) -> bool:
        span = self.functions[fqn].span
        return (
            self.indegree.get(fqn, 0) == 0
            and not fqn.endswith(MODULE_SUFFIX)
            and "migrations" not in span.file.split("/")
        )

    def flows(self) -> list[dict[str, Any]]:
        sized = []
        for fqn in self.functions:
            if self.is_root(fqn):
                members = self.closure(fqn)
                if len(members) >= 2:
                    sized.append((len(members), fqn, members))
        sized.sort(key=lambda item: (-item[0], item[1]))
        return [self.flow(size, fqn) for size, fqn, _ in sized[:MAX_FLOWS]]

    def flow(self, size: int, fqn: str) -> dict[str, Any]:
        ordered = self.ordered(fqn)
        ext = sorted({m for f in ordered for m in self.externals.get(f, ())})
        return {
            **symbol(fqn, self.functions[fqn]),
            "id": fqn,
            "size": size,
            "members": ordered,
            "steps": self.steps(fqn),
            "files": list(dict.fromkeys(self.functions[f].span.file for f in ordered)),
            "externals": ext[:MAX_EXTERNALS],
        }


def is_call(caller: str) -> bool:
    return not caller.endswith(MODULE_SUFFIX)


def external_module(fqn: str) -> str:
    dotted = fqn[len("ext:"):]
    return dotted.rsplit(".", 1)[0] if "." in dotted else dotted


def symbol(fqn: str, record: Any, depth: int | None = None) -> dict[str, Any]:
    span = record.span
    out: dict[str, Any] = {"fqn": fqn, "file": span.file, "line": span.line, "end_line": span.end_line}
    if depth is not None:
        out["depth"] = depth
    return out
