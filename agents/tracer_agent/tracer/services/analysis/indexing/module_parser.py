import ast

from tracer.models.index_records import FunctionRecord, ModuleRecord
from tracer.services.analysis.indexing.annotation_resolver import AnnotationResolver
from tracer.services.analysis.indexing.class_extractor import ClassExtractor
from tracer.services.analysis.indexing.function_extractor import FunctionExtractor
from tracer.services.analysis.indexing.import_binding_extractor import (
    ImportBindingExtractor,
)
from tracer.services.analysis.indexing.module_function_synthesizer import (
    ModuleFunctionSynthesizer,
)
from tracer.services.analysis.syntax.paths import module_fqn
from tracer.services.analysis.syntax.types import ClassAnalysis


class ModuleParseResult:
    def __init__(
        self,
        module: ModuleRecord,
        classes: tuple[ClassAnalysis, ...],
        functions: tuple[FunctionRecord, ...],
        source_roots: frozenset[str] = frozenset(),
    ) -> None:
        self.module = module
        self.classes = classes
        self.functions = functions
        self.source_roots = source_roots


class ModuleParser:
    def __init__(
        self,
        class_extractor: ClassExtractor,
        function_extractor: FunctionExtractor,
        module_function_synthesizer: ModuleFunctionSynthesizer,
    ) -> None:
        self._class_extractor = class_extractor
        self._function_extractor = function_extractor
        self._module_function_synthesizer = module_function_synthesizer

    def parse(self, relpath: str, source: str, project_modules: frozenset[str]) -> ModuleParseResult:
        tree = ast.parse(source)
        fqn = module_fqn(relpath)
        binder = ImportBindingExtractor(relpath, fqn, project_modules)
        binder.visit(tree)
        local_names = frozenset(
            stmt.name
            for stmt in tree.body
            if isinstance(stmt, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        )
        resolver = AnnotationResolver(binder.bindings, local_names, fqn)

        class_analyses: list[ClassAnalysis] = []
        functions: list[FunctionRecord] = []
        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef):
                analysis = self._class_extractor.extract(stmt, fqn, resolver, relpath)
                class_analyses.append(analysis)
                for item in stmt.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        functions.append(
                            self._function_extractor.extract(item, fqn, analysis.record.fqn, resolver, relpath)
                        )
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._function_extractor.extract(stmt, fqn, None, resolver, relpath))
        functions.append(self._module_function_synthesizer.synthesize(tree, fqn, relpath))

        module = ModuleRecord(
            fqn=fqn,
            bindings=dict(sorted(binder.bindings.items())),
            classes=tuple(sorted(a.record.fqn for a in class_analyses)),
            functions=tuple(sorted(f.fqn for f in functions if f.cls is None)),
        )
        return ModuleParseResult(
            module, tuple(class_analyses), tuple(functions), frozenset(binder.source_roots)
        )
