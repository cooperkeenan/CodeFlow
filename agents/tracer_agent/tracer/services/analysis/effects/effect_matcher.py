import ast
from collections.abc import Mapping
from dataclasses import dataclass

from tracer.services.analysis.effects.effect_registry import (
    BOTO_METHOD_KINDS,
    RULES,
    LibraryRule,
)
from tracer.services.analysis.effects.effect_target_extractor import (
    EffectTargetExtractor,
)

from shared.models.flow_graph import EffectKind

_WRITE_MODES = ("w", "a", "x")


@dataclass(frozen=True)
class EffectMatch:
    kind: EffectKind
    target: str
    method: str


class CallEffectMatcher:
    def __init__(self, extractor: EffectTargetExtractor) -> None:
        self._extractor = extractor

    def match(
        self, node: ast.Call, ext_roots: frozenset[str], constants: Mapping[str, str]
    ) -> EffectMatch | None:
        method_name = self._method_name(node.func)
        for rule in RULES:
            if rule.roots.isdisjoint(ext_roots):
                continue
            if not self._method_ok(rule, method_name):
                continue
            if "builtins" in rule.roots and not self._is_write_open(node):
                continue
            kind = self._resolve_kind(rule, method_name)
            target = self._extractor.extract(rule.target, node, constants)
            method = method_name.upper() if kind == "http_out" else ""
            return EffectMatch(kind=kind, target=target, method=method)
        return None

    def _method_ok(self, rule: LibraryRule, method_name: str) -> bool:
        if not rule.methods and not rule.method_prefix:
            return True
        if method_name in rule.methods:
            return True
        return bool(rule.method_prefix) and method_name.startswith(rule.method_prefix)

    def _resolve_kind(self, rule: LibraryRule, method_name: str) -> EffectKind:
        if rule.target == "boto":
            return BOTO_METHOD_KINDS.get(method_name, rule.kind)
        return rule.kind

    def _is_write_open(self, node: ast.Call) -> bool:
        mode = self._open_mode(node)
        return bool(mode) and mode[0] in _WRITE_MODES

    def _open_mode(self, node: ast.Call) -> str:
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            second = node.args[1].value
            return second if isinstance(second, str) else ""
        for keyword in node.keywords:
            if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                value = keyword.value.value
                return value if isinstance(value, str) else ""
        return ""

    def _method_name(self, func: ast.expr) -> str:
        if isinstance(func, ast.Attribute):
            return func.attr
        if isinstance(func, ast.Name):
            return func.id
        return ""
