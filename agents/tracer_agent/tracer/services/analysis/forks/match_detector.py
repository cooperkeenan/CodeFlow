import ast

from tracer.models.call_records import Arm
from tracer.models.index_records import FunctionRecord
from tracer.models.sites import DispatchSite
from tracer.services.analysis.contracts import DispatchDetectionContext
from tracer.services.analysis.resolve.indexes import CallSiteArmIndex
from tracer.services.analysis.syntax.block_walker import walk_statements
from tracer.services.analysis.syntax.call_expr_split import truncated_source
from tracer.services.analysis.syntax.selector_reads_extractor import selector_reads
from tracer.services.analysis.syntax.terminal_classifier import classify_terminal

from shared.models.flow_graph import SourceRef


class MatchDetector:
    def detect(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]:
        arm_index = CallSiteArmIndex(context.callsites)
        sites: list[DispatchSite] = []
        for record in context.index.functions.values():
            for stmt, block, index in walk_statements(record.body.body):
                if not isinstance(stmt, ast.Match):
                    continue
                sites.append(self._build_site(record, stmt, index < len(block) - 1, arm_index))
        return tuple(sites)

    def _build_site(
        self, record: FunctionRecord, node: ast.Match, reconverges: bool, arm_index: CallSiteArmIndex
    ) -> DispatchSite:
        site_id = f"{record.fqn}:{node.lineno}"
        arms = tuple(
            Arm(
                index=i,
                label_source=self._case_label(case)[:120],
                callsites=arm_index.callsites_for(site_id, i),
                terminal=classify_terminal(case.body),
            )
            for i, case in enumerate(node.cases)
        )
        return DispatchSite(
            id=site_id,
            owner=record.fqn,
            kind="match",
            selector_source=truncated_source(node.subject)[:120],
            selector_reads=selector_reads(node.subject),
            arms=arms,
            reconverges=reconverges,
            span=SourceRef(
                file=record.span.file, line=node.lineno, end_line=node.end_lineno or node.lineno
            ),
        )

    def _case_label(self, case: ast.match_case) -> str:
        pattern = ast.unparse(case.pattern)
        if case.guard is not None:
            return f"case {pattern} if {ast.unparse(case.guard)}"
        return f"case {pattern}"
