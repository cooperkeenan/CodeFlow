import ast

from models.function_record import FunctionRecord
from models.module_record import ModuleRecord

from services.analysis.annotation_resolver import AnnotationResolver
from services.analysis.class_analysis import ClassAnalysis
from services.analysis.class_extractor import ClassExtractor
from services.analysis.function_extractor import FunctionExtractor
from services.analysis.import_binding_extractor import ImportBindingExtractor
from services.analysis.module_function_synthesizer import ModuleFunctionSynthesizer
from services.analysis.path_fqn import module_fqn


class ModuleParseResult:
    def __init__(
        self, module: ModuleRecord, classes: tuple[ClassAnalysis, ...], functions: tuple[FunctionRecord, ...]
    ) -> None:
        self.module = module
        self.classes = classes
        self.functions = functions


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
        return ModuleParseResult(module, tuple(class_analyses), tuple(functions))
