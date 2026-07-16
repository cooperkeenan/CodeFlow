import ast

from models.arm import Arm
from models.dispatch_site import DispatchSite
from models.function_record import FunctionRecord
from services.analysis.block_walker import walk_statements
from services.analysis.callsite_arm_index import CallSiteArmIndex
from services.analysis.dispatch_detector import DispatchDetectionContext
from services.analysis.terminal_classifier import classify_terminal
from shared.models.flow_graph import SourceRef


class ExceptDetector:
    def detect(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]:
        arm_index = CallSiteArmIndex(context.callsites)
        sites: list[DispatchSite] = []
        for record in context.index.functions.values():
            for stmt, block, index in walk_statements(record.body.body):
                if not isinstance(stmt, ast.Try):
                    continue
                site = self._build_site(record, stmt, index < len(block) - 1, arm_index)
                if site is not None:
                    sites.append(site)
        return tuple(sites)

    def _build_site(
        self, record: FunctionRecord, node: ast.Try, reconverges: bool, arm_index: CallSiteArmIndex
    ) -> DispatchSite | None:
        site_id = f"{record.fqn}:{node.lineno}"
        arms = [
            Arm(
                index=0,
                label_source="try",
                callsites=arm_index.callsites_for(site_id, 0),
                terminal=classify_terminal(node.body),
            )
        ]
        for i, handler in enumerate(node.handlers):
            arms.append(
                Arm(
                    index=i + 1,
                    label_source=self._handler_label(handler),
                    callsites=arm_index.callsites_for(site_id, i + 1),
                    terminal=classify_terminal(handler.body),
                )
            )
        if not any(arm.callsites for arm in arms[1:]):
            return None
        return DispatchSite(
            id=site_id,
            owner=record.fqn,
            kind="except",
            selector_source="try",
            selector_reads=(),
            arms=tuple(arms),
            reconverges=reconverges,
            span=SourceRef(
                file=record.span.file, line=node.lineno, end_line=node.end_lineno or node.lineno
            ),
        )

    def _handler_label(self, handler: ast.ExceptHandler) -> str:
        if handler.type is None:
            return "*"
        return ast.unparse(handler.type)[:120]
