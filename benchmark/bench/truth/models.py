import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

BUILDER_VERSION = "1"

RUNTIME_CONFIDENCE = 1.0
STATIC_CONFIDENCE = 0.8


@dataclass(frozen=True, order=True)
class RouteFact:
    """One registered route, in canonical form.

    `provenance` records how this fact was established: ``runtime:<framework>``
    means the framework's own resolver was asked, ``static:ast`` means an
    independent parser inferred it. The distinction is published in results so a
    reader can see how much of a score rests on the stronger method.
    """

    canonical: str
    handler: str
    provenance: str
    confidence: float


@dataclass(frozen=True)
class GroundTruth:
    repo: str
    sha: str
    built_at: str
    builder_version: str
    entry_point_status: str
    routes: tuple[RouteFact, ...]
    branch_sites: int
    notes: tuple[str, ...]

    @property
    def canonical_routes(self) -> frozenset[str]:
        return frozenset(route.canonical for route in self.routes)

    def provenance_mix(self) -> dict[str, int]:
        return dict(sorted(Counter(route.provenance for route in self.routes).items()))

    def to_dict(self) -> dict:
        return {
            "repo": self.repo,
            "sha": self.sha,
            "built_at": self.built_at,
            "builder_version": self.builder_version,
            "entry_point_status": self.entry_point_status,
            "branch_sites": self.branch_sites,
            "provenance_mix": self.provenance_mix(),
            "routes": [asdict(route) for route in sorted(self.routes)],
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroundTruth":
        return cls(
            repo=data["repo"],
            sha=data["sha"],
            built_at=data["built_at"],
            builder_version=data["builder_version"],
            entry_point_status=data["entry_point_status"],
            routes=tuple(RouteFact(**route) for route in data.get("routes", [])),
            branch_sites=int(data.get("branch_sites", 0)),
            notes=tuple(data.get("notes", [])),
        )


class TruthMismatch(RuntimeError):
    """Committed ground truth does not match the checked-out corpus commit."""


class TruthStore:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def path_for(self, repo: str, sha: str) -> Path:
        return self._directory / f"{repo}@{sha[:12]}.json"

    def exists(self, repo: str, sha: str) -> bool:
        return self.path_for(repo, sha).exists()

    def write(self, truth: GroundTruth) -> Path:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self.path_for(truth.repo, truth.sha)
        path.write_text(json.dumps(truth.to_dict(), indent=2, sort_keys=True) + "\n")
        return path

    def read(self, repo: str, sha: str) -> GroundTruth:
        path = self.path_for(repo, sha)
        if not path.exists():
            raise TruthMismatch(
                f"No ground truth for {repo}@{sha[:12]}. Run `bench truth build --repo {repo}`.\n"
                "Scoring without ground truth would silently produce a meaningless number."
            )
        truth = GroundTruth.from_dict(json.loads(path.read_text()))
        if truth.sha != sha:
            raise TruthMismatch(
                f"{repo}: ground truth was built at {truth.sha[:12]} but the corpus is "
                f"pinned at {sha[:12]}. Rebuild ground truth."
            )
        return truth
