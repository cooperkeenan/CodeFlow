import ast

from models.arm import Arm
from models.dispatch_site import DispatchSite
from models.function_record import FunctionRecord
from services.analysis.block_walker import walk_statements
from services.analysis.call_expr_split import truncated_source
from services.analysis.callsite_arm_index import CallSiteArmIndex
from services.analysis.callsite_caller_index import CallSiteCallerIndex
from services.analysis.dispatch_detector import DispatchDetectionContext
from services.analysis.selector_reads_extractor import selector_reads
from services.analysis.terminal_classifier import classify_terminal
from shared.models.flow_graph import SourceRef

_ChainArm = tuple[str, int, list[ast.stmt], str]


class BranchDetector:
    def detect(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]:
        arm_index = CallSiteArmIndex(context.callsites)
        caller_index = CallSiteCallerIndex(context.callsites)
        sites: list[DispatchSite] = []
        for record in context.index.functions.values():
            sites.extend(self._detect_in_function(record, arm_index))
            sites.extend(self._detect_ternaries(record, caller_index))
        return tuple(sites)

    def _detect_in_function(self, record: FunctionRecord, arm_index: CallSiteArmIndex) -> list[DispatchSite]:
        sites: list[DispatchSite] = []
        consumed: set[int] = set()
        for stmt, block, index in walk_statements(record.body.body):
            if not isinstance(stmt, ast.If) or id(stmt) in consumed:
                continue
            chain, has_else = self._chain(stmt, record.fqn, consumed)
            sites.append(
                self._build_site(record, stmt, chain, has_else, index < len(block) - 1, arm_index)
            )
        return sites

    def _chain(self, node: ast.If, owner: str, consumed: set[int]) -> tuple[list[_ChainArm], bool]:
        site_id = f"{owner}:{node.lineno}"
        arms: list[_ChainArm] = [(site_id, 0, node.body, truncated_source(node.test)[:120])]
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            consumed.add(id(node.orelse[0]))
            nested, has_else = self._chain(node.orelse[0], owner, consumed)
            arms.extend(nested)
            return arms, has_else
        if node.orelse:
            arms.append((site_id, 1, node.orelse, "else"))
            return arms, True
        return arms, False

    def _build_site(
        self,
        record: FunctionRecord,
        root: ast.If,
        chain: list[_ChainArm],
        has_else: bool,
        reconverges: bool,
        arm_index: CallSiteArmIndex,
    ) -> DispatchSite:
        arms = [
            Arm(
                index=i,
                label_source=label,
                callsites=arm_index.callsites_for(site_id, f03_index),
                terminal=classify_terminal(body),
            )
            for i, (site_id, f03_index, body, label) in enumerate(chain)
        ]
        if not has_else:
            arms.append(Arm(index=len(arms), label_source="else", callsites=(), terminal="falls_through"))
        return DispatchSite(
            id=f"{record.fqn}:{root.lineno}",
            owner=record.fqn,
            kind="branch",
            selector_source=truncated_source(root.test)[:120],
            selector_reads=selector_reads(root.test),
            arms=tuple(arms),
            reconverges=reconverges,
            span=SourceRef(
                file=record.span.file, line=root.lineno, end_line=root.end_lineno or root.lineno
            ),
        )

    def _detect_ternaries(self, record: FunctionRecord, caller_index: CallSiteCallerIndex) -> list[DispatchSite]:
        sites: list[DispatchSite] = []
        for node in ast.walk(record.body):
            if not isinstance(node, ast.IfExp):
                continue
            if not (self._has_call(node.body) or self._has_call(node.orelse) or self._has_call(node.test)):
                continue
            sites.append(self._build_ternary_site(record, node, caller_index))
        return sites

    def _has_call(self, node: ast.expr) -> bool:
        return any(isinstance(n, ast.Call) for n in ast.walk(node))

    def _build_ternary_site(
        self, record: FunctionRecord, node: ast.IfExp, caller_index: CallSiteCallerIndex
    ) -> DispatchSite:
        all_calls = caller_index.callsites_for(record.fqn)
        then_lines = {n.lineno for n in ast.walk(node.body) if isinstance(n, ast.Call)}
        else_lines = {n.lineno for n in ast.walk(node.orelse) if isinstance(n, ast.Call)}
        arms = (
            Arm(
                index=0,
                label_source=truncated_source(node.body)[:120],
                callsites=tuple(c for c in all_calls if c.line in then_lines),
                terminal="falls_through",
            ),
            Arm(
                index=1,
                label_source=truncated_source(node.orelse)[:120],
                callsites=tuple(c for c in all_calls if c.line in else_lines),
                terminal="falls_through",
            ),
        )
        return DispatchSite(
            id=f"{record.fqn}:{node.lineno}",
            owner=record.fqn,
            kind="branch",
            selector_source=truncated_source(node.test)[:120],
            selector_reads=selector_reads(node.test),
            arms=arms,
            reconverges=True,
            span=SourceRef(
                file=record.span.file, line=node.lineno, end_line=node.end_lineno or node.lineno
            ),
        )
