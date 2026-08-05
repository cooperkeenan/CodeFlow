# PBI 56 — Emit the full graph with visibility levels (stop deleting decisions)

**Model: implement with Sonnet.** Backend only — do not touch `frontend/`.

## Why

`PageBudgeter` currently **destroys** decisions to fit a 40-node page. Measured on the demo repo
`django-helpdesk` (`/Users/cooperkeenan/github/django-helpdesk`):

| Stage | Nodes | Decisions |
|---|---|---|
| After `FlowCondenser` + `FlowStitcher` (pre-budget) | 253 | **222** |
| After `PageBudgeter` (what ships today) | 43 | **8** |

So the decisions *do* reach the graph — 222 of the 225 the judge finds. The budget stage deletes
214 of them. `DecisionDissolver._contract` is the worst offender: it removes the decision **and
every node reachable only through it**.

The next feature is progressive disclosure: one always-visible high-level diagram, with `+`/`−`
per branch splicing the in-between decisions in place. That needs the detail to *exist*. Folding
must become **reversible metadata, not deletion**.

## The shape to implement

From the user's reference sketch — grey = outcomes, orange = decisions, **orange is what `+`
reveals**:

```
collapsed:   Orchestrator ─────────────────────► Regulatory Agent
expanded:    Orchestrator ──► (Correct Product ID?) ──► Regulatory Agent
```

A decision is an **edge annotation that gets promoted to a node on expand**. It is not a hidden
node that gets shown — modelling it that way forces a full page relayout on every toggle.

This gives one flat, deterministic rule:

- **Level 0 (skeleton, always visible):** `entry`, `step`, `parallel`, `effect` nodes — the outcomes.
- **Level 1 (revealed on expand):** every `decision` node.

A decision that forks to two outcomes appears in the `hidden_path` of **both** skeleton edges. The
frontend dedupes by node id on expand, which reconstructs the fork exactly as the sketch draws it.

## Scope

### 1. Model — `shared/models/flow_graph.py`

```python
class FlowNode(BaseModel):
    ...
    level: int = 0

class FlowEdge(BaseModel):
    ...
    hidden_path: list[str] = []
```

`level` 0 = skeleton, 1 = revealed. `hidden_path` is the **ordered** list of node ids spliced onto
that edge when it is expanded; empty on an edge that hides nothing. Leave `_sort_canonical`'s sort
keys as they are.

### 2. `SkeletonProjector` (new file, tracer analysis)

Given the full `BudgetWorkGraph`, with `S` = the set of non-`decision` node ids:

- For every `A ∈ S`, walk the full graph from `A`. For every path `A → h₁ → … → hₙ → B` where
  `B ∈ S` and every `hᵢ ∉ S`, emit a skeleton edge `A → B` carrying `hidden_path = [h₁ … hₙ]`.
- Stop each walk at the first node in `S` — do not walk through skeleton nodes.
- If `A → B` is already a direct edge in the full graph, keep it with `hidden_path = []`.
- Bound the walk (suggest depth ≤ 8) so a cyclic region cannot hang the run; drop paths that exceed
  it rather than truncating them.
- Deterministic: iterate sorted ids, sort candidate paths on `(len(path), path)` and keep the
  shortest per `(A, B)`; break ties on the id tuple.

### 3. `VisibilityBudgeter` (new file) replacing `PageBudgeter` in the pipeline

Order of operations:

1. `BudgetRecondenser.recondense` — merge adjacent step chains (unchanged, still wanted).
2. `ArmFolder.fold` — cap arms per decision (unchanged).
3. `EffectCapper.cap` — dedupe/collapse effects (unchanged).
4. `SkeletonProjector` — compute the level-0 edge set with `hidden_path`.
5. Emit a `FlowGraph` whose **nodes are every node** (decisions marked `level=1`, the rest
   `level=0`) and whose **edges are the union** of the projected skeleton edges and the full
   graph's own edges. Both sets are needed: the skeleton edges drive the collapsed view, the full
   edges drive the expanded one.

`LaneApportioner`, `SpineProtector`, `BudgetConfig.node_budget` and `visible_decisions` no longer
gate what survives. **Do not delete decisions anywhere.**

### 4. Retire the destructive path

After the swap nothing references these — delete them:
`page_budgeter.py`, `page_budgeter_factory.py`, `decision_admitter.py`, `decision_dissolver.py`,
`lane_reducer.py`. Add a `build_visibility_budgeter` factory in their place and update
`flow_pipeline.py`, `scripts/render_repo.py` and any other import site.

Keep: `budget_work_graph.py`, `budget_recondenser.py`, `arm_folder.py`, `effect_capper.py`,
`budget_config.py`, `lane_apportioner.py`, `spine_protector.py`.

### 5. Invariants — `budget_invariants.py`

The old assertions (node ceiling, ≥1 arm per decision) no longer apply and must **not** be silently
dropped; replace them with the invariants that do apply to the new model:

- every node is reachable from some `entry` when hidden paths are expanded;
- every id in every `hidden_path` exists and has `level == 1`;
- every skeleton edge's endpoints have `level == 0`;
- expanding every `hidden_path` reproduces a connected graph — no level-1 node is orphaned.

Assert these; do not weaken them to go green.

## Acceptance

Run from the repo root with `source venv/bin/activate`:

```bash
python scripts/render_repo.py /Users/cooperkeenan/github/django-helpdesk /tmp/hd
python scripts/render_repo.py /Users/cooperkeenan/github/django-helpdesk /tmp/hd2
diff /tmp/hd/flow_graph.json /tmp/hd2/flow_graph.json     # MUST be empty
python scripts/selfrun.py                                  # 5 assertions must pass
```

Then, on `/tmp/hd/flow_graph.json`:

1. **Decisions survive** — `level == 1` decision nodes ≈ **222**, not 8. This is the headline number.
2. **Skeleton is small** — `level == 0` nodes ≈ 30–45, dominated by `entry` + `step`.
3. **Decisions are annotations** — at least half of the level-1 decisions appear in at least one
   edge's `hidden_path`. Report the exact count of decisions reachable via some `hidden_path`; a
   decision in no hidden path is unreachable in the UI and is a defect worth reporting honestly.
4. **Determinism** — the `diff` above is byte-empty.
5. `python scripts/screenshot_flow.py /Users/cooperkeenan/github/django-helpdesk` still renders
   without error. The picture will not improve yet — the frontend has no expand control. It must
   not regress into overlap or an empty canvas.

Report the real numbers for 1–3 even if they disappoint. Do not tune a threshold to make them look
better.

## Constraints

`CLAUDE.md` is law: ≤150 lines/file, one class per file, constructor injection, type annotations on
all signatures, no docstrings or explanatory comments, no unsolicited tests, no unused imports.
Determinism: sort every set/dict iteration, break ties on `(file, line, name)`. No prompt changes,
so no `PROMPT_VERSION` bump. Do not touch `frontend/`.
