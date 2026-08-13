import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

EntryPointTruth = Literal["objective", "none"]


class UnpinnedCorpus(RuntimeError):
    """Raised rather than scoring against a corpus that can move."""


@dataclass(frozen=True)
class ProbeSpec:
    """How to boot a repo so its own framework can be asked what it registers.

    `env` is the boot configuration used for the probe. It is committed rather than
    inferred because routes can depend on it — a router mounted inside
    `if settings.ENVIRONMENT == "local"` exists under one configuration and not
    another, so the configuration is part of the ground truth's meaning.
    """

    kind: str
    settings_module: str | None = None
    app_path: str | None = None
    distribution: str | None = None
    source_root: str | None = None
    env: tuple[tuple[str, str], ...] = ()

    @property
    def env_map(self) -> dict[str, str]:
        return dict(self.env)


@dataclass(frozen=True)
class CorpusRepo:
    name: str
    url: str
    ref: str
    condition: str
    frameworks: tuple[str, ...]
    entry_point_truth: EntryPointTruth
    probe: ProbeSpec
    control: bool
    hypothesis: str


@dataclass(frozen=True)
class Pin:
    name: str
    url: str
    sha: str
    resolved_at: str


@dataclass(frozen=True)
class PinnedRepo:
    repo: CorpusRepo
    pin: Pin

    @property
    def name(self) -> str:
        return self.repo.name

    @property
    def slug(self) -> str:
        return f"{self.repo.name}@{self.pin.sha[:12]}"


def _probe_from(raw: dict[str, Any] | None) -> ProbeSpec:
    data = raw or {"kind": "none"}
    env = data.get("env") or {}
    return ProbeSpec(
        kind=str(data.get("kind", "none")),
        settings_module=data.get("settings_module"),
        app_path=data.get("app_path"),
        distribution=data.get("distribution"),
        source_root=data.get("source_root"),
        env=tuple(sorted((str(k), str(v)) for k, v in env.items())),
    )


def _repo_from(raw: dict[str, Any]) -> CorpusRepo:
    return CorpusRepo(
        name=str(raw["name"]),
        url=str(raw["url"]),
        ref=str(raw["ref"]),
        condition=str(raw.get("condition", "")),
        frameworks=tuple(raw.get("frameworks") or ()),
        entry_point_truth=raw.get("entry_point_truth", "none"),
        probe=_probe_from(raw.get("probe")),
        control=bool(raw.get("control", False)),
        hypothesis=str(raw.get("hypothesis", "")).strip(),
    )


class CorpusLoader:
    def __init__(self, corpus_path: Path, lock_path: Path) -> None:
        self._corpus_path = corpus_path
        self._lock_path = lock_path

    def load(self) -> tuple[CorpusRepo, ...]:
        raw = yaml.safe_load(self._corpus_path.read_text())
        repos = [_repo_from(entry) for entry in raw.get("repos", [])]
        return tuple(sorted(repos, key=lambda repo: repo.name))

    def get(self, name: str) -> CorpusRepo:
        for repo in self.load():
            if repo.name == name:
                return repo
        known = ", ".join(repo.name for repo in self.load())
        raise KeyError(f"unknown repo {name!r}; corpus contains: {known}")

    def pins(self) -> dict[str, Pin]:
        if not self._lock_path.exists():
            return {}
        raw = json.loads(self._lock_path.read_text() or "{}")
        return {
            name: Pin(name=name, url=data["url"], sha=data["sha"], resolved_at=data["resolved_at"])
            for name, data in sorted(raw.get("pins", {}).items())
        }

    def pinned(self, name: str) -> PinnedRepo:
        repo = self.get(name)
        pin = self.pins().get(name)
        if pin is None:
            raise UnpinnedCorpus(
                f"{name} has no pinned commit. Run `bench corpus pin --repo {name}` first. "
                "Scoring against an unpinned corpus is not reproducible."
            )
        return PinnedRepo(repo=repo, pin=pin)

    def write_pins(self, pins: dict[str, Pin]) -> None:
        merged = {name: pin for name, pin in self.pins().items()}
        merged.update(pins)
        payload = {
            "version": 1,
            "pins": {
                name: {"url": pin.url, "sha": pin.sha, "resolved_at": pin.resolved_at}
                for name, pin in sorted(merged.items())
            },
        }
        self._lock_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
