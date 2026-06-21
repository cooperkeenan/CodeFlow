# PBI 23 — Structural comparison harness + scorecard CLI

**Batch:** 5 &nbsp;|&nbsp; **Depends on:** PBI 22 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
Turn "eyeball the UI" into a per-stage score on every run, so accuracy regressions are visible as
numbers and CI-checkable.

## Scope

### 1. Harness — `evaluation/compare.py` (CLI)
Load the latest `shared/outputs/*.json` (profiler / tracer / layout) and the answer-sheet fixture
(PBI 22), then compute and print a scorecard:
- **Modules:** precision / recall of module-name set vs `modules`.
- **Cross-module edges:** recall of `expected_cross_module_edges` (collapse component edges to owning
  modules via the zones mapping). This surfaces the missing `frontend→api` edge.
- **Orchestrators / entry points:** how many expected ones are present.
- **Component counts:** per-module count inside its range (flags the `frontend` JS-not-traced gap).

Print a readable table per stage + an overall score, and **exit non-zero** when the overall score is
below a threshold (so it can gate CI). Constructor-inject comparator dependencies; split helpers
(loader, comparators, scorecard printer) to keep each file ≤150 lines. No new agent/LLM calls.

### 2. Invocation
Runnable as e.g. `python -m evaluation.compare` against whatever is currently in `shared/outputs/`.
Document the one-line invocation at the top of the README's Batch 5 section.

## Acceptance criteria
- Running the CLI after `/analyse` prints a structural scorecard for the current run.
- The known gaps appear as misses: `frontend→api` edge absent, `frontend` component count below range.
- Introducing a regression (e.g. a dropped module) visibly lowers the relevant score and the exit code.

## Out of scope
- The fixture itself (PBI 22). Changing pipeline behaviour to *fix* any miss — this only measures.
