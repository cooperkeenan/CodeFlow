import ast

from models.arm import Arm
from models.dispatch_site import DispatchSite
from models.function_record import FunctionRecord
from services.analysis.callsite_caller_index import CallSiteCallerIndex
from services.analysis.dispatch_detector import DispatchDetectionContext
from services.analysis.route_prefix_index import RoutePrefixIndex
from services.analysis.terminal_classifier import classify_terminal
from shared.models.flow_graph import SourceRef

_FACTORY_NAMES = {"APIRouter", "FastAPI"}
_VERBS = {"get", "post", "put", "delete", "patch"}


class FastApiRouteScanner:
    def scan(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]:
        prefixes = RoutePrefixIndex(context.index)
        caller_index = CallSiteCallerIndex(context.callsites)
        sites: list[DispatchSite] = []
        for module_fqn in context.index.modules:
            module_record = context.index.functions.get(f"{module_fqn}.<module>")
            if module_record is None:
                continue
            handlers = [
                r
                for r in context.index.functions.values()
                if r.module == module_fqn and r.cls is None and r.name != "<module>"
            ]
            for router_var, router_line in self._routers(module_record):
                arms = self._arms(module_fqn, router_var, handlers, prefixes, caller_index)
                if arms:
                    sites.append(self._build_site(module_record, router_var, router_line, arms))
        return tuple(sites)

    def _routers(self, module_record: FunctionRecord) -> list[tuple[str, int]]:
        found: list[tuple[str, int]] = []
        for stmt in module_record.body.body:
            if not (isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call)):
                continue
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                continue
            if self._factory_name(stmt.value) in _FACTORY_NAMES:
                found.append((stmt.targets[0].id, stmt.lineno))
        return found

    def _factory_name(self, call: ast.Call) -> str | None:
        func = call.func
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None

    def _arms(
        self,
        module_fqn: str,
        router_var: str,
        handlers: list[FunctionRecord],
        prefixes: RoutePrefixIndex,
        caller_index: CallSiteCallerIndex,
    ) -> tuple[Arm, ...]:
        prefix = prefixes.prefix_for(f"{module_fqn}.{router_var}")
        arms: list[Arm] = []
        for handler in handlers:
            match = self._route_decorator(handler, router_var)
            if match is None:
                continue
            verb, path = match
            arms.append(
                Arm(
                    index=len(arms),
                    label_source=f"{verb.upper()} {prefix}{path}",
                    callsites=caller_index.callsites_for(handler.fqn),
                    terminal=classify_terminal(handler.body.body),
                )
            )
        return tuple(arms)

    def _route_decorator(self, handler: FunctionRecord, router_var: str) -> tuple[str, str] | None:
        for dec in handler.body.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            if not isinstance(dec.func.value, ast.Name) or dec.func.value.id != router_var:
                continue
            if dec.func.attr not in _VERBS or not dec.args:
                continue
            arg = dec.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return dec.func.attr, arg.value
        return None

    def _build_site(
        self, module_record: FunctionRecord, router_var: str, router_line: int, arms: tuple[Arm, ...]
    ) -> DispatchSite:
        return DispatchSite(
            id=f"{module_record.fqn}:{router_line}",
            owner=module_record.fqn,
            kind="route",
            selector_source=router_var,
            selector_reads=(),
            arms=arms,
            reconverges=False,
            span=SourceRef(file=module_record.span.file, line=router_line, end_line=router_line),
        )
