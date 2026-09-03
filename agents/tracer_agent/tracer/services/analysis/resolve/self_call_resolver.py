from tracer.models.call_records import ResolvedTarget
from tracer.services.analysis.resolve.attribute_path_resolver import (
    AttributePathResolver,
)
from tracer.services.analysis.resolve.construction_site_index import (
    ConstructionSiteIndex,
)
from tracer.services.analysis.resolve.dependency_param_mapper import (
    DependencyParamMapper,
)
from tracer.services.analysis.resolve.direct_attr_type_index import DirectAttrTypeIndex
from tracer.services.analysis.resolve.mro_method_finder import MroMethodFinder


class SelfCallResolver:
    def __init__(
        self,
        mro: MroMethodFinder,
        attribute_path: AttributePathResolver,
        param_mapper: DependencyParamMapper,
        construction_index: ConstructionSiteIndex,
        direct_attrs: DirectAttrTypeIndex,
    ) -> None:
        self._mro = mro
        self._attribute_path = attribute_path
        self._param_mapper = param_mapper
        self._construction_index = construction_index
        self._direct_attrs = direct_attrs

    def resolve(self, owner_class_fqn: str, chain: list[str]) -> tuple[ResolvedTarget, ...] | None:
        if not chain:
            return None
        if len(chain) == 1:
            target = self._mro.find_method(owner_class_fqn, chain[0])
            return (ResolvedTarget(target, "resolved"),) if target else None
        attr = chain[0]
        dep_type = self._mro.find_attr_type(owner_class_fqn, attr) or self._direct_attrs.get(owner_class_fqn, attr)
        if dep_type is None:
            return None
        resolved = self._attribute_path.resolve(dep_type, chain[1:])
        if resolved is not None:
            return resolved
        return self._construction_fallback(owner_class_fqn, attr, chain[1:])

    def _construction_fallback(
        self, owner_class_fqn: str, attr: str, remaining_chain: list[str]
    ) -> tuple[ResolvedTarget, ...] | None:
        param = self._param_mapper.param_for_attr(owner_class_fqn, attr)
        if param is None:
            return None
        concrete = self._construction_index.concrete_for(owner_class_fqn, param)
        if concrete is None:
            return None
        return self._attribute_path.resolve(concrete, remaining_chain)
