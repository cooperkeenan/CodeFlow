"""Mechanical guarantee that ground truth is built without CodeFlow present.

Ground truth derived from CodeFlow's own output would make the benchmark measure
nothing. That is prevented structurally rather than by discipline: this module is
imported by every ground-truth entry point and refuses to proceed if any CodeFlow
analysis module has been loaded or is reachable on sys.path.
"""

import sys
from pathlib import Path

_BENCHMARK_DIR_NAME = "benchmark"
_SUBJECT_PACKAGE_DIRS = ("agents", "api", "shared")


class ContaminatedTruthBuild(RuntimeError):
    """CodeFlow was importable or imported while building ground truth."""


def _loaded_subject_modules(codeflow_root: Path) -> list[str]:
    root = codeflow_root.resolve()
    benchmark_root = root / _BENCHMARK_DIR_NAME
    offenders: list[str] = []
    for name, module in list(sys.modules.items()):
        raw = getattr(module, "__file__", None)
        if not raw:
            continue
        try:
            path = Path(raw).resolve()
        except (OSError, ValueError):
            continue
        if not path.is_relative_to(root) or path.is_relative_to(benchmark_root):
            continue
        if path.parts[len(root.parts)] in _SUBJECT_PACKAGE_DIRS:
            offenders.append(name)
    return sorted(offenders)


def _reachable_subject_paths(codeflow_root: Path) -> list[str]:
    """Any sys.path entry inside the CodeFlow tree but outside benchmark/.

    Matching on directory *names* is not enough: CodeFlow's own scripts make their
    analysis code importable by inserting `agents/tracer_agent`, which is named
    neither `agents` nor `api` nor `shared`. Anything reachable inside the subject
    tree is treated as contamination.
    """
    root = codeflow_root.resolve()
    benchmark_root = root / _BENCHMARK_DIR_NAME
    reachable: list[str] = []
    for entry in sys.path:
        try:
            path = Path(entry or ".").resolve()
        except (OSError, ValueError):
            continue
        if path.is_relative_to(root) and not path.is_relative_to(benchmark_root):
            reachable.append(str(path))
    return sorted(set(reachable))


def assert_uncontaminated(codeflow_root: Path) -> None:
    """Raise unless this process is free of CodeFlow analysis code."""
    loaded = _loaded_subject_modules(codeflow_root)
    reachable = _reachable_subject_paths(codeflow_root)
    if not loaded and not reachable:
        return

    details = []
    if loaded:
        details.append("imported CodeFlow modules: " + ", ".join(loaded[:10]))
    if reachable:
        details.append("CodeFlow paths on sys.path: " + ", ".join(reachable[:5]))
    raise ContaminatedTruthBuild(
        "Refusing to build Tier 1 ground truth in a process that can see CodeFlow.\n"
        + "\n".join(f"  - {line}" for line in details)
        + "\nGround truth must be a fact about the repository, established without "
        "the tool under test. Build it in a separate process."
    )
