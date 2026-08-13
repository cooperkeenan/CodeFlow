from pathlib import Path

from bench.config.corpus_model import PinnedRepo
from bench.truth._guard import assert_uncontaminated
from bench.truth.models import (
    BUILDER_VERSION,
    RUNTIME_CONFIDENCE,
    GroundTruth,
    RouteFact,
)
from bench.truth.normalize import RouteNormalizer
from bench.truth.runtime.probe_runner import ProbeOutcome, RuntimeProbe
from bench.truth.static.branch_census import BranchCensus
from bench.truth.static.fastapi_routes import FastApiRouteExtractor
from bench.truth.static.py_files import load_tree

STATIC_EXTRACTORS = ("fastapi",)


class GroundTruthBuilder:
    """Establishes Tier 1 ground truth for one pinned repository.

    Runtime introspection is primary: the framework's own resolver is the strongest
    available answer to "what does this repo register". Static extraction is a
    fallback, and which one produced each fact is recorded on the fact itself.
    """

    def __init__(
        self,
        normalizer: RouteNormalizer,
        fastapi_extractor: FastApiRouteExtractor,
        census: BranchCensus,
        probe: RuntimeProbe,
        codeflow_root: Path,
    ) -> None:
        self._normalizer = normalizer
        self._fastapi = fastapi_extractor
        self._census = census
        self._probe = probe
        self._codeflow_root = codeflow_root

    def build(self, pinned: PinnedRepo, repo_path: Path, built_at: str) -> GroundTruth:
        assert_uncontaminated(self._codeflow_root)

        tree = load_tree(repo_path)
        census = self._census.count(tree)
        notes: list[str] = []

        if pinned.repo.entry_point_truth == "none":
            routes: list[RouteFact] = []
            notes.append(
                "This repository has no objective register of entry points (a library's "
                "public API is a convention, not a fact). It is excluded from the "
                "entry-point metric rather than scored against an invented ground truth."
            )
        else:
            routes, route_notes = self._routes(pinned, repo_path, tree)
            notes.extend(route_notes)

        if census.unparsed:
            notes.append(
                f"{len(census.unparsed)} file(s) failed to parse and are absent from the "
                f"branch census: {', '.join(census.unparsed[:5])}"
            )

        return GroundTruth(
            repo=pinned.name,
            sha=pinned.pin.sha,
            built_at=built_at,
            builder_version=BUILDER_VERSION,
            entry_point_status=pinned.repo.entry_point_truth,
            routes=tuple(sorted(routes)),
            branch_sites=census.total,
            notes=tuple(notes),
        )

    def _routes(
        self, pinned: PinnedRepo, repo_path: Path, tree
    ) -> tuple[list[RouteFact], list[str]]:
        spec = pinned.repo.probe
        if self._probe.supports(spec):
            outcome = self._probe.run(pinned.slug, repo_path, spec)
            if outcome.ok:
                return self._from_probe(outcome, spec.kind), [
                    f"Routes established by runtime introspection ({spec.kind}) using the "
                    f"boot configuration recorded in corpus.yaml: {sorted(spec.env_map)}."
                ]
            return self._fallback(pinned, tree, outcome)
        return self._fallback(pinned, tree, None)

    def _from_probe(self, outcome: ProbeOutcome, kind: str) -> list[RouteFact]:
        facts: list[RouteFact] = []
        for route in outcome.routes:
            methods = tuple(route.get("methods") or ())
            for canonical in self._normalizer.expand(methods, str(route.get("path", ""))):
                facts.append(
                    RouteFact(
                        canonical=canonical,
                        handler=str(route.get("endpoint", "")),
                        provenance=f"runtime:{kind}",
                        confidence=RUNTIME_CONFIDENCE,
                    )
                )
        return facts

    def _fallback(
        self, pinned: PinnedRepo, tree, outcome: ProbeOutcome | None
    ) -> tuple[list[RouteFact], list[str]]:
        notes: list[str] = []
        reason = outcome.failure_reason if outcome else "no runtime probe for this repo"
        notes.append(
            f"Runtime introspection unavailable ({reason}); ground truth falls back to "
            "independent static extraction. Treat these facts as weaker evidence."
        )

        frameworks = pinned.repo.frameworks
        if "fastapi" in frameworks:
            facts, extract_notes = self._fastapi.extract(tree)
            return facts, notes + extract_notes

        supported = ", ".join(STATIC_EXTRACTORS) or "none"
        notes.append(
            f"No static route extractor implemented for {frameworks or ('unknown',)}; "
            f"implemented: {supported}. Route ground truth for this repo is EMPTY, which "
            "would make any score against it meaningless. It must be excluded, not scored."
        )
        return [], notes
