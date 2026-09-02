import ast
from collections.abc import Mapping

from tracer.models.index_records import FunctionRecord
from tracer.services.analysis.effects.effect_registry import ROUTE_VERBS

_DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


class RouteHandlerInspector:
    def inspect(self, record: FunctionRecord, bindings: Mapping[str, str]) -> str | None:
        body = record.body
        if not isinstance(body, _DEF_NODES):
            return None
        for decorator in body.decorator_list:
            if self._is_route(decorator):
                return self._response_target(decorator, bindings, record)
        return None

    def _is_route(self, decorator: ast.expr) -> bool:
        return (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr in ROUTE_VERBS
        )

    def _response_target(
        self, decorator: ast.Call, bindings: Mapping[str, str], record: FunctionRecord
    ) -> str:
        for keyword in decorator.keywords:
            if keyword.arg == "response_model" and isinstance(keyword.value, ast.Name):
                return bindings.get(keyword.value.id, keyword.value.id)
        return record.returns or ""
