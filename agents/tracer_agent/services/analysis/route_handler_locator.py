import ast

from models.function_record import FunctionRecord
from models.project_index import ProjectIndex

_DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
_VERBS = frozenset({"get", "post", "put", "delete", "patch", "head", "options"})


class RouteHandlerLocator:
    def __init__(self, index: ProjectIndex) -> None:
        self._index = index

    def locate(self, owner_module: str, verb: str, path: str) -> str | None:
        candidates = [
            record
            for record in self._index.functions.values()
            if record.module == owner_module and record.cls is None and record.name != "<module>"
        ]
        for record in candidates:
            decorated = self._decorator_path(record)
            if decorated is not None and decorated[0] == verb and path.endswith(decorated[1]):
                return record.fqn
        return None

    def _decorator_path(self, record: FunctionRecord) -> tuple[str, str] | None:
        if not isinstance(record.body, _DEF_NODES):
            return None
        for dec in record.body.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            if dec.func.attr not in _VERBS or not dec.args:
                continue
            arg = dec.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return dec.func.attr, arg.value
        return None
