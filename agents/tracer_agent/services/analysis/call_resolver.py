import ast

from models.call_site import CallSite
from models.function_record import FunctionRecord
from models.project_index import ProjectIndex
from models.resolved_target import ResolvedTarget
from services.analysis.annotation_normalizer import normalize_type
from services.analysis.attribute_path_resolver import AttributePathResolver
from services.analysis.call_expr_split import truncated_source
from services.analysis.call_site_visitor import CallSiteVisitor
from services.analysis.call_target_resolver import CallTargetResolver
from services.analysis.construction_site_index import ConstructionSiteIndex
from services.analysis.dependency_param_mapper import DependencyParamMapper
from services.analysis.direct_attr_type_index import DirectAttrTypeIndex
from services.analysis.local_binding_collector import LocalBindingCollector
from services.analysis.module_local_names import local_names_of
from services.analysis.module_scope_resolver import ModuleScopeResolver
from services.analysis.mro_method_finder import MroMethodFinder
from services.analysis.self_call_resolver import SelfCallResolver
from services.analysis.self_expr_type_resolver import SelfExprTypeResolver
from services.analysis.tier_counter import TierCounter
from services.analysis.unique_name_index import UniqueNameIndex

_DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


class CallResolver:
    def __init__(self, index: ProjectIndex) -> None:
        self._index = index
        mro = MroMethodFinder(index)
        attribute_path = AttributePathResolver(index, mro)
        self._self_resolver = SelfCallResolver(
            mro, attribute_path, DependencyParamMapper(index), ConstructionSiteIndex(index),
            DirectAttrTypeIndex(index),
        )
        self._attribute_path = attribute_path
        self._unique_names = UniqueNameIndex(index)
        self._local_binder = LocalBindingCollector(attribute_path, index)
        self.tier_counter = TierCounter()

    def resolve_project(self) -> tuple[CallSite, ...]:
        sites: list[CallSite] = []
        module_scopes = self._build_module_scopes()
        module_bindings = self._build_module_bindings(module_scopes)
        for record in self._index.functions.values():
            scope = module_scopes.get(record.module)
            if scope is None:
                continue
            self_types = SelfExprTypeResolver(record.cls, self._self_resolver, self._index)
            local_bindings = dict(module_bindings.get(record.module, {}))
            local_bindings.update(self._param_bindings(record))
            local_bindings.update(self._local_binder.collect(record.body, scope, self_types))
            resolver = CallTargetResolver(
                record, scope, local_bindings, self._attribute_path, self._self_resolver,
                self._unique_names, self.tier_counter, self._index,
            )
            visitor = CallSiteVisitor(record.fqn, resolver, self._index)
            visitor.visit(record.body)
            sites.extend(visitor.sites)
            sites.extend(self._decorator_sites(record, scope))
        return tuple(sites)

    def _param_bindings(self, record: FunctionRecord) -> dict[str, str]:
        bindings: dict[str, str] = {}
        for param in record.params:
            normalized = normalize_type(param.annotation, self._index)
            if normalized is not None:
                bindings[param.name] = normalized
        return bindings

    def _build_module_scopes(self) -> dict[str, ModuleScopeResolver]:
        return {
            fqn: ModuleScopeResolver(module.bindings, local_names_of(module), fqn, self._index)
            for fqn, module in self._index.modules.items()
        }

    def _build_module_bindings(self, module_scopes: dict[str, ModuleScopeResolver]) -> dict[str, dict[str, str]]:
        result: dict[str, dict[str, str]] = {}
        for record in self._index.functions.values():
            if record.name != "<module>":
                continue
            scope = module_scopes.get(record.module)
            if scope is not None:
                result[record.module] = self._local_binder.collect(record.body, scope)
        return result

    def _decorator_sites(self, record: FunctionRecord, scope: ModuleScopeResolver) -> list[CallSite]:
        if not isinstance(record.body, _DEF_NODES):
            return []
        sites: list[CallSite] = []
        for dec in record.body.decorator_list:
            resolved = scope.resolve_node(dec)
            if resolved is None or resolved.startswith("ext:") or resolved not in self._index.functions:
                continue
            sites.append(
                CallSite(
                    caller=record.fqn,
                    line=dec.lineno,
                    targets=(ResolvedTarget(resolved, "inferred"),),
                    context=(),
                    in_loop=False,
                    call_source=truncated_source(dec),
                )
            )
        return sites
