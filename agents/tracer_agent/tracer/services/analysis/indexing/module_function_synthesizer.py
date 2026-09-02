import ast

from tracer.models.index_records import FunctionRecord

from shared.models.flow_graph import SourceRef

_EXCLUDED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)


class ModuleFunctionSynthesizer:
    def synthesize(self, tree: ast.Module, module_fqn: str, relpath: str) -> FunctionRecord:
        body = [stmt for stmt in tree.body if not isinstance(stmt, _EXCLUDED)]
        synthetic = ast.Module(body=body, type_ignores=[])
        end_line = tree.body[-1].end_lineno if tree.body else 1
        return FunctionRecord(
            fqn=f"{module_fqn}.<module>",
            module=module_fqn,
            cls=None,
            name="<module>",
            params=(),
            returns=None,
            span=SourceRef(file=relpath, line=1, end_line=end_line or 1),
            is_async=False,
            decorators=(),
            body=synthetic,
        )
