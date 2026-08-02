from collections.abc import Mapping

from models.class_record import ClassRecord
from models.function_record import FunctionRecord
from models.module_record import ModuleRecord
from models.project_index import ProjectIndex

from services.analysis.module_parser import ModuleParser
from services.analysis.path_fqn import module_fqn
from services.analysis.protocol_implementation_resolver import ProtocolImplementationResolver
from services.analysis.subclass_index_builder import SubclassIndexBuilder


class ProjectIndexer:
    def __init__(
        self,
        module_parser: ModuleParser,
        subclass_index_builder: SubclassIndexBuilder,
        protocol_implementation_resolver: ProtocolImplementationResolver,
    ) -> None:
        self._module_parser = module_parser
        self._subclass_index_builder = subclass_index_builder
        self._protocol_implementation_resolver = protocol_implementation_resolver

    def index(self, files: Mapping[str, str]) -> ProjectIndex:
        project_modules = frozenset(module_fqn(relpath) for relpath in files)
        modules: dict[str, ModuleRecord] = {}
        classes: dict[str, ClassRecord] = {}
        functions: dict[str, FunctionRecord] = {}
        all_analyses = []
        source_roots: set[str] = set()
        for relpath in sorted(files):
            result = self._module_parser.parse(relpath, files[relpath], project_modules)
            modules[result.module.fqn] = result.module
            source_roots |= result.source_roots
            for analysis in result.classes:
                classes[analysis.record.fqn] = analysis.record
                all_analyses.append(analysis)
            for record in result.functions:
                functions[record.fqn] = record

        nominal = self._subclass_index_builder.build(all_analyses)
        structural = self._protocol_implementation_resolver.build(all_analyses)
        return ProjectIndex(
            modules=dict(sorted(modules.items())),
            classes=dict(sorted(classes.items())),
            functions=dict(sorted(functions.items())),
            implementations_index=self._merge(nominal, structural),
            sources=files,
            source_roots=frozenset(source_roots),
        )

    def _merge(
        self, nominal: Mapping[str, tuple[str, ...]], structural: Mapping[str, tuple[str, ...]]
    ) -> dict[str, tuple[str, ...]]:
        merged: dict[str, tuple[str, ...]] = {}
        for fqn in set(nominal) | set(structural):
            merged[fqn] = tuple(sorted(set(nominal.get(fqn, ())) | set(structural.get(fqn, ()))))
        return dict(sorted(merged.items()))
