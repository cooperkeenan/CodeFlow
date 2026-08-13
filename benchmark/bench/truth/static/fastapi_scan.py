import ast
from dataclasses import dataclass, field

VERBS = frozenset({"get", "post", "put", "delete", "patch", "head", "options", "trace"})
UNRESOLVED = "\x00UNRESOLVED"

APP_FACTORIES = frozenset({"FastAPI"})
ROUTER_FACTORIES = frozenset({"APIRouter"})


@dataclass(frozen=True)
class DecoratedRoute:
    router_var: str
    path: str
    methods: tuple[str, ...]
    handler: str
    line: int


@dataclass(frozen=True)
class Include:
    parent_var: str
    target: str
    prefix: str


@dataclass
class ModuleFacts:
    module: str
    imports: dict[str, str] = field(default_factory=dict)
    apps: set[str] = field(default_factory=set)
    routers: dict[str, str] = field(default_factory=dict)
    routes: list[DecoratedRoute] = field(default_factory=list)
    includes: list[Include] = field(default_factory=list)


def _package_of(module: str) -> str:
    return module.rsplit(".", 1)[0] if "." in module else ""


def _resolve_relative(module: str, level: int) -> str:
    base = _package_of(module) if level == 1 else module
    for _ in range(max(0, level - 1)):
        base = _package_of(base)
    return base


def _literal(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = [p.value for p in node.values if isinstance(p, ast.Constant)]
        return "".join(str(p) for p in parts) if len(parts) == len(node.values) else None
    return None


def _dotted(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


class ModuleScanner(ast.NodeVisitor):
    """Collects FastAPI router/app declarations and route decorators for one module."""

    def __init__(self, module: str) -> None:
        self.facts = ModuleFacts(module=module)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.facts.imports[alias.asname or alias.name.split(".")[0]] = alias.name

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        base = node.module or ""
        if node.level:
            prefix = _resolve_relative(self.facts.module, node.level)
            base = f"{prefix}.{base}" if base else prefix
        for alias in node.names:
            target = f"{base}.{alias.name}" if base else alias.name
            self.facts.imports[alias.asname or alias.name] = target

    def visit_Assign(self, node: ast.Assign) -> None:
        if not isinstance(node.value, ast.Call):
            return self.generic_visit(node)
        factory = _dotted(node.value.func) or ""
        name = factory.rsplit(".", 1)[-1]
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if name in APP_FACTORIES:
                self.facts.apps.add(target.id)
                self.facts.routers[target.id] = ""
            elif name in ROUTER_FACTORIES:
                self.facts.routers[target.id] = self._prefix_arg(node.value)
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        call = node.value
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
            if call.func.attr == "include_router" and call.args:
                parent = _dotted(call.func.value)
                target = _dotted(call.args[0])
                if parent and target:
                    self.facts.includes.append(
                        Include(parent_var=parent, target=target, prefix=self._prefix_arg(call))
                    )
        self.generic_visit(node)

    def _prefix_arg(self, call: ast.Call) -> str:
        for keyword in call.keywords:
            if keyword.arg == "prefix":
                value = _literal(keyword.value)
                return UNRESOLVED if value is None else value
        return ""

    def _record(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue
            verb = decorator.func.attr.lower()
            if verb not in VERBS or not decorator.args:
                continue
            router = _dotted(decorator.func.value)
            path = _literal(decorator.args[0])
            if router is None or path is None:
                continue
            self.facts.routes.append(
                DecoratedRoute(
                    router_var=router,
                    path=path,
                    methods=(verb.upper(),),
                    handler=f"{self.facts.module}.{node.name}",
                    line=node.lineno,
                )
            )
        self.generic_visit(node)

    visit_FunctionDef = _record
    visit_AsyncFunctionDef = _record
