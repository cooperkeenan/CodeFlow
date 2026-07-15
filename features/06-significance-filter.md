# F06 — Significance filter & ranking

Depends on: F03, F04
Deliverable: `agents/tracer_agent/services/analysis/significance_filter.py`
(+ `reach_computer.py`, `site_scorer.py`)

## Why

This is the `if s != null` vs `if s == "cat"` problem, solved deterministically. It
decides which dispatch sites are real crossroads, which are guards, and which are
noise — with zero LLM involvement.

## Spec

### 1. Utility damping (compute first)

A component (class, or module for free functions) is a **utility** iff its fan-in —
count of *distinct calling functions* across the project — is ≥ `max(8, P90 of all
fan-ins)`. Utilities (config, logger wrappers, base stores used everywhere) are
excluded from reach sets below; otherwise every arm "reaches" them and distinctness
collapses. The utility set is part of the output (layout may gray them into a footer).

### 2. Reach sets

For each arm: BFS over F03 edges (confidence `resolved` + `inferred` only) from the
arm's callsites, depth ≤ 6, collecting **project components** (owning class fqn, or
module fqn for free functions), minus utilities, minus the owner's own component.
Memoize per-function reach; SCCs share one memo entry.

### 3. Arm classification

- `void`: empty reach set.
- `guard`: `terminal ∈ {raises, returns, continues}` **and** reach ≤ 2 components.
  (Catches `if not match: raise ValueError(...)` and error-alert arms — even ones
  that call a distinct notifier.)
- `live`: everything else.

### 4. Site classification

- kinds `route`, `table`, `polymorphic`: **decision** by construction if ≥2 arms
  (they are dispatch by structure); `dynamic`: decision iff its owner is reachable
  from an entry (F07 tells us; provisionally keep).
- kinds `branch`, `match`, `except`: let L = live arms.
  - **decision** iff |L| ≥ 2 and the live arms pairwise satisfy **mutual exclusivity
    of reach**: each has ≥1 component the other lacks (neither reach set is a subset
    of the other).
  - **guarded_step** iff |L| == 1 and ≥1 guard arm: not a node — the guard becomes a
    `guarded` badge (+ exit annotation) on the step that absorbs the live arm.
  - **noise** otherwise: dissolved; arms' callsites rejoin the surrounding flow.

### 5. Score (ranking among decisions)

```
score = 3.0 * log2(1 + |union of live-arm reach sets|)
      + 2.0 * provenance          # selector_reads: 2 if any read is a param of a
                                  #   route-handler-reachable function's signature
                                  #   (entry data), 1 if any param at all, 0 internal
      + 2.0 * (not reconverges)   # the branch decides the rest of the story
      + 1.0 * (kind in {route, table, polymorphic})
```

Provenance "entry data" is computed cheaply: a param whose owning function is a route
handler, or whose value is passed (one call level) from a route handler's param.
Ties break on `(owner, span.line)`. Output: every site tagged
decision/guarded_step/noise, decisions in total score order.

## Non-goals

No node budget (F09). No taint analysis beyond the one-level param provenance. The
weights are constants in one config dataclass — no tuning UI.

## Acceptance

On CodeFlow: every `if not X: raise/return` in validators classifies **guard**;
`ServiceStepPlanner.plan`'s except-site classifies **decision** (try arm reaches
validator+LLM path, handler arm reaches `_fallback` — mutually exclusive reach);
route sites rank above internal branches; `ServiceStepValidator`'s allowed-type
conditional classifies **noise** or **guard**, never decision. Print the ranked
decision table with per-arm reach sizes for manual review.
