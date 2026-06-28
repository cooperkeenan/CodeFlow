"""Structural scorecard for a CodeFlow run.

Usage:
    python -m evaluation.compare

Loads shared/outputs/tracer.json (or tracer_output.json) and compares it against
evaluation/answer_sheet/codeflow.json.  Exits non-zero when overall score < 50%.
"""
import sys

from evaluation.comparators import (
    compare_component_counts,
    compare_edges,
    compare_entry_points,
    compare_modules,
)
from evaluation.loader import load_fixture, load_spec
from evaluation.scorecard import print_scorecard

_PASS_THRESHOLD = 0.5


def main() -> None:
    spec = load_spec()
    fixture = load_fixture()
    results = {
        "modules": compare_modules(spec, fixture),
        "edges": compare_edges(spec, fixture),
        "entry_points": compare_entry_points(spec, fixture),
        "component_counts": compare_component_counts(spec, fixture),
    }
    overall = print_scorecard(results)
    sys.exit(0 if overall >= _PASS_THRESHOLD else 1)


if __name__ == "__main__":
    main()
