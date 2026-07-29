import ast

from models.arm import Arm
from models.call_site import CallSite
from models.dispatch_site import DispatchSite
from models.resolved_target import ResolvedTarget
from services.analysis.dispatch_detector import DispatchDetectionContext
from services.analysis.selector_reads_extractor import selector_reads
from shared.models.flow_graph import SourceRef


class PolymorphicDetector:
    def detect(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]:
        return tuple(
            self._build_site(site, context)
            for site in context.callsites
            if len(site.targets) >= 2
        )

    def _build_site(self, site: CallSite, context: DispatchDetectionContext) -> DispatchSite:
        arms = tuple(
            Arm(
                index=i,
                label_source=self._class_name(target.fqn),
                callsites=(self._narrowed(site, target),),
                terminal="falls_through",
            )
            for i, target in enumerate(site.targets)
        )
        owner_record = context.index.functions.get(site.caller)
        file = owner_record.span.file if owner_record is not None else ""
        return DispatchSite(
            id=f"{site.caller}:{site.line}",
            owner=site.caller,
            kind="polymorphic",
            selector_source=site.call_source[:120],
            selector_reads=self._selector_reads(site.call_source),
            arms=arms,
            reconverges=True,
            span=SourceRef(file=file, line=site.line, end_line=site.line),
        )

    def _narrowed(self, site: CallSite, target: ResolvedTarget) -> CallSite:
        return CallSite(
            caller=site.caller,
            line=site.line,
            targets=(target,),
            context=site.context,
            in_loop=site.in_loop,
            call_source=site.call_source,
        )

    def _class_name(self, fqn: str) -> str:
        parts = fqn.split(".")
        return parts[-2] if len(parts) >= 2 else fqn

    def _selector_reads(self, call_source: str) -> tuple[str, ...]:
        try:
            parsed = ast.parse(call_source, mode="eval")
        except SyntaxError:
            return ()
        if isinstance(parsed.body, ast.Call):
            return selector_reads(parsed.body.func)
        return ()
