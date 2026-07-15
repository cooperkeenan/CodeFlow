import ast

from models.function_record import FunctionRecord
from models.param_record import ParamRecord
from shared.models.flow_graph import SourceRef

from services.analysis.annotation_resolver import AnnotationResolver

_SKIP_PARAMS = {"self", "cls"}


class FunctionExtractor:
    def extract(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        module_fqn: str,
        cls_fqn: str | None,
        resolver: AnnotationResolver,
        relpath: str,
    ) -> FunctionRecord:
        prefix = cls_fqn or module_fqn
        fqn = f"{prefix}.{node.name}"
        params = tuple(
            ParamRecord(name=arg.arg, annotation=resolver.resolve(arg.annotation))
            for arg in self._all_args(node)
            if arg.arg not in _SKIP_PARAMS
        )
        return FunctionRecord(
            fqn=fqn,
            module=module_fqn,
            cls=cls_fqn,
            name=node.name,
            params=params,
            returns=resolver.resolve(node.returns),
            span=SourceRef(file=relpath, line=node.lineno, end_line=node.end_lineno or node.lineno),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            decorators=tuple(resolver.resolve(dec) or "" for dec in node.decorator_list),
            body=node,
        )

    def _all_args(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.arg]:
        args = node.args
        extra = ([args.vararg] if args.vararg else []) + ([args.kwarg] if args.kwarg else [])
        return args.posonlyargs + args.args + args.kwonlyargs + extra
