import ast
import re
from collections.abc import Mapping

_SQL_TABLE = re.compile(r"(?:FROM|INTO|UPDATE)\s+(\w+)", re.IGNORECASE)
_BOTO_KEYS = {"QueueUrl", "Bucket", "TopicArn"}


class EffectTargetExtractor:
    def extract(self, strategy: str, node: ast.Call, constants: Mapping[str, str]) -> str:
        if strategy == "url":
            return self._url(node)
        if strategy == "model":
            return self._model(node, constants)
        if strategy == "sql":
            return self._sql(node, constants)
        if strategy == "path":
            return self._path(node)
        if strategy == "boto":
            return self._boto(node)
        return ""

    def _url(self, node: ast.Call) -> str:
        if not node.args:
            return ""
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        if isinstance(arg, ast.JoinedStr):
            return self._fstring_path(arg)
        if isinstance(arg, ast.Name):
            return arg.id
        return ""

    def _fstring_path(self, node: ast.JoinedStr) -> str:
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                stripped = part.value.lstrip("/")
                if stripped:
                    return f"/{stripped}"
        return ""

    def _model(self, node: ast.Call, constants: Mapping[str, str]) -> str:
        for keyword in node.keywords:
            if keyword.arg == "model":
                return self._string_of(keyword.value, constants)
        return ""

    def _sql(self, node: ast.Call, constants: Mapping[str, str]) -> str:
        if not node.args:
            return ""
        match = _SQL_TABLE.search(self._string_of(node.args[0], constants))
        return match.group(1) if match else ""

    def _path(self, node: ast.Call) -> str:
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value
        return ""

    def _boto(self, node: ast.Call) -> str:
        for keyword in node.keywords:
            if keyword.arg in _BOTO_KEYS and isinstance(keyword.value, ast.Constant):
                return str(keyword.value.value)
        return ""

    def _string_of(self, node: ast.expr, constants: Mapping[str, str]) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return constants.get(node.id, node.id)
        return ""
