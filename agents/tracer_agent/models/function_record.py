import ast
from dataclasses import dataclass, field

from models.param_record import ParamRecord
from shared.models.flow_graph import SourceRef


@dataclass(frozen=True)
class FunctionRecord:
    fqn: str
    module: str
    cls: str | None
    name: str
    params: tuple[ParamRecord, ...]
    returns: str | None
    span: SourceRef
    is_async: bool
    decorators: tuple[str, ...]
    body: ast.AST = field(repr=False, compare=False)
