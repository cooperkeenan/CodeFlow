from collections.abc import Sequence

from services.analysis.class_analysis import ClassAnalysis


class ProtocolImplementationResolver:
    def build(self, analyses: Sequence[ClassAnalysis]) -> dict[str, tuple[str, ...]]:
        protocols = [a for a in analyses if a.is_protocol and a.method_names]
        concretes = [a for a in analyses if not a.is_abstract]
        result: dict[str, tuple[str, ...]] = {}
        for protocol in protocols:
            matches = sorted(
                candidate.record.fqn
                for candidate in concretes
                if candidate.record.fqn != protocol.record.fqn
                and protocol.method_names <= candidate.method_names
            )
            if matches:
                result[protocol.record.fqn] = tuple(matches)
        return result
