import ast

from models.arm import Arm
from models.dispatch_site import DispatchSite
from models.function_record import FunctionRecord
from models.project_index import ProjectIndex
from services.analysis.dispatch_detector import DispatchDetectionContext
from services.analysis.django_url_pattern_parser import (
    include_target,
    is_include,
    route_view,
    urlpatterns_lists,
)
from services.analysis.django_view_resolver import DjangoViewResolver
from services.analysis.module_local_names import local_names_of
from services.analysis.module_scope_resolver import ModuleScopeResolver
from services.analysis.mro_method_finder import MroMethodFinder
from services.analysis.path_fqn import resolve_absolute
from shared.models.flow_graph import SourceRef

_UrlConf = tuple[FunctionRecord, tuple[ast.List, ...]]


class DjangoRouteScanner:
    def scan(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]:
        index = context.index
        resolver = DjangoViewResolver(index, MroMethodFinder(index))
        scopes: dict[str, ModuleScopeResolver] = {}
        urlconfs: dict[str, _UrlConf] = {}
        for module_fqn, module in index.modules.items():
            record = index.functions.get(f"{module_fqn}.<module>")
            if record is None:
                continue
            lists = urlpatterns_lists(record)
            if lists:
                urlconfs[module_fqn] = (record, lists)
                scopes[module_fqn] = ModuleScopeResolver(
                    module.bindings, local_names_of(module), module_fqn, index
                )
        included = self._included_modules(urlconfs, index)
        sites: list[DispatchSite] = []
        for module_fqn in sorted(urlconfs):
            if module_fqn in included:
                continue
            record, lists = urlconfs[module_fqn]
            arms: list[Arm] = []
            for urllist in lists:
                arms.extend(
                    self._collect_arms(
                        urllist, module_fqn, scopes, urlconfs, index,
                        resolver, "", frozenset(), len(arms),
                    )
                )
            if arms:
                sites.append(self._build_site(module_fqn, record, lists[0].lineno, arms))
        return tuple(sites)

    def _build_site(
        self, module_fqn: str, record: FunctionRecord, line: int, arms: list[Arm]
    ) -> DispatchSite:
        return DispatchSite(
            id=f"{module_fqn}.urlpatterns:{line}",
            owner=module_fqn,
            kind="route",
            selector_source="urlpatterns",
            selector_reads=(),
            arms=tuple(arms),
            reconverges=False,
            span=SourceRef(file=record.span.file, line=line, end_line=line),
        )

    def _included_modules(self, urlconfs: dict[str, _UrlConf], index: ProjectIndex) -> frozenset[str]:
        project_modules = frozenset(index.modules.keys())
        found: set[str] = set()
        for module_fqn, (_, lists) in urlconfs.items():
            for urllist in lists:
                for element in urllist.elts:
                    parsed = route_view(element)
                    if parsed is None or not is_include(parsed[1]):
                        continue
                    target = include_target(parsed[1])
                    if target is not None:
                        resolved = resolve_absolute(target, module_fqn, project_modules)
                        if resolved in urlconfs:
                            found.add(resolved)
        return frozenset(found)

    def _collect_arms(
        self,
        urllist: ast.List,
        module_fqn: str,
        scopes: dict[str, ModuleScopeResolver],
        urlconfs: dict[str, _UrlConf],
        index: ProjectIndex,
        resolver: DjangoViewResolver,
        prefix: str,
        visited: frozenset[str],
        offset: int = 0,
    ) -> list[Arm]:
        arms: list[Arm] = []
        scope = scopes[module_fqn]
        for element in urllist.elts:
            parsed = route_view(element)
            if parsed is None:
                continue
            route, view = parsed
            full_path = prefix + route
            if is_include(view):
                arms.extend(
                    self._nested_arms(view, module_fqn, full_path, scopes, urlconfs, index, resolver, visited)
                )
                continue
            arms.extend(resolver.arms_for(full_path, view, scope, offset + len(arms)))
        return arms

    def _nested_arms(
        self,
        include_call: ast.Call,
        module_fqn: str,
        prefix: str,
        scopes: dict[str, ModuleScopeResolver],
        urlconfs: dict[str, _UrlConf],
        index: ProjectIndex,
        resolver: DjangoViewResolver,
        visited: frozenset[str],
    ) -> list[Arm]:
        target = include_target(include_call)
        if target is None:
            return []
        resolved = resolve_absolute(target, module_fqn, frozenset(index.modules.keys()))
        if resolved not in urlconfs or resolved in visited:
            return []
        _, nested_assign = urlconfs[resolved]
        return self._collect_arms(
            nested_assign.value, resolved, scopes, urlconfs, index, resolver, prefix, visited | {resolved}
        )
