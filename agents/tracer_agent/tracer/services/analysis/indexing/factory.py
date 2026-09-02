from tracer.services.analysis.indexing.attr_type_collector import AttrTypeCollector
from tracer.services.analysis.indexing.class_extractor import ClassExtractor
from tracer.services.analysis.indexing.function_extractor import FunctionExtractor
from tracer.services.analysis.indexing.module_function_synthesizer import (
    ModuleFunctionSynthesizer,
)
from tracer.services.analysis.indexing.module_parser import ModuleParser
from tracer.services.analysis.indexing.project_indexer import ProjectIndexer
from tracer.services.analysis.indexing.protocol_implementation_resolver import (
    ProtocolImplementationResolver,
)
from tracer.services.analysis.indexing.subclass_index_builder import (
    SubclassIndexBuilder,
)


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
