# F09 — One-page budget

Depends on: F06, F07, F08
Deliverable: `agents/tracer_agent/services/analysis/page_budgeter.py`

## Why

One page replaces drill-down. The page must stay readable for any repo size, and it
must show the SAME content on every run. Granularity therefore adapts by folding the
least significant structure back into steps — deterministically.

## Spec

Config (one frozen dataclass): `node_budget B = 36`, `max_arms_per_decision A = 5`,
`min_lane_nodes = 3`.

### 1. Apportion

`lane_budget_i = max(min_lane_nodes, floor(B * lane.mass_i / Σ mass))`, remainder
(from flooring) granted to lanes in mass order. Lanes are never dropped — a service
with one entry still shows `entry → step → effect`.

### 2. Admit decisions

Per lane, admit decisions in F06 score order while the lane's projected node count
(entries + admitted decisions + the steps/effects their admission implies, computed
by re-condensation preview) fits the lane budget. A non-admitted decision **dissolves
exactly like F06 noise**: its arms' content merges into the surrounding step, and the
step gains `folded_count += arms`.

### 3. Fold wide arms

For every admitted decision with more than `A` arms (route tables, big match
ladders): keep the top `A-1` arms by arm reach size, plus one synthetic arm labeled
`+N more` (`folded_count = N`) whose target is a step backed by the folded arms'
components. Route-table entries folded this way still count as entries for stitching
(a stitch may target the folded step).

### 4. Re-condense & effects cap

Re-run F07's step-merging after folding. Effects dedupe per (lane, kind, target);
more than 3 identical-kind effects in one lane collapse into one node with
`folded_count`.

### 5. Invariants (assert, don't hope)

- `len(nodes) ≤ B + len(lanes) * min_lane_nodes` (hard ceiling);
- every decision node retains ≥2 outgoing arm edges;
- every node reachable from some entry;
- stitch edges never dangle (both ends survived, else drop the edge — the effect
  leaf remains);
- output canonical-sorted per F01, byte-identical across runs.

## Non-goals

No user-facing depth control, no interactive expansion — folding is final for the
page. (If a future feature wants a depth slider, it filters THIS output client-side;
the budget stays server-deterministic.)

## Acceptance

CodeFlow fits in the default budget with zero folding except route tables if any
agent exceeds `A` routes. Synthetic check: feed a fabricated index with 200 decisions
across 3 lanes; assert the invariants hold, the same 36±(3·lanes) nodes survive on
repeated runs, and lowering B strictly removes the lowest-scored decisions first.
