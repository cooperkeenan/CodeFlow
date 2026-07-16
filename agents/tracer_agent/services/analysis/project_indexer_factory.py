from services.analysis.attr_type_collector import AttrTypeCollector
from services.analysis.class_extractor import ClassExtractor
from services.analysis.function_extractor import FunctionExtractor
from services.analysis.module_function_synthesizer import ModuleFunctionSynthesizer
from services.analysis.module_parser import ModuleParser
from services.analysis.project_indexer import ProjectIndexer
from services.analysis.protocol_implementation_resolver import ProtocolImplementationResolver
from services.analysis.subclass_index_builder import SubclassIndexBuilder


def build_project_indexer() -> ProjectIndexer:
    return ProjectIndexer(
        ModuleParser(
            ClassExtractor(AttrTypeCollector()),
            FunctionExtractor(),
            ModuleFunctionSynthesizer(),
        ),
        SubclassIndexBuilder(),
        ProtocolImplementationResolver(),
    )
