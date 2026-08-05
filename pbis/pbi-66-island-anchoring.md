# PBI 66 — Unreachable islands crash the pipeline; establish I2 instead of only asserting it

The pipeline asserts that every node is reachable from an entry, but **nothing establishes it**.
When condensation produces a self-contained cluster with no path from any entry, the run dies at
the assert. This takes the whole product down on real repos.

**Frontend changes are NOT authorized.** Backend only.

---

## 1. The failure

Reported from a platform run on a repo laid out `app/<service>/src`:

```
File "agents/tracer_agent/services/analysis/budget_invariants.py", line 45, in _assert_reachable
AssertionError: 10 nodes unreachable from any entry:
  ['dec:app.regulatory_agent.src.tools.cci_edit_tool.CCIEditTool.get_cci_info:57',
   'dec:app.regulatory_agent.src.tools.mue_edit_tool.MueEditTool.get_mue_edit_info:47',
   'eff:app.regulatory_agent.src.services.data_platform_service.DataPlatformClient.fetch:37', ...]
```

**It reproduces locally on CodeFlow itself** — use this, you do not need the reporter's repo:

```bash
python scripts/render_repo.py . /tmp/cf_repro     # crashes: 8 nodes unreachable
python scripts/render_repo.py --no-llm . /tmp/cf  # passes
```

## 2. Root cause — confirmed, not guessed

The stranded nodes are **not orphans**. They form a fully connected island. On CodeFlow the whole
`RouteMatcher.match` body is a closed cluster of exactly 8 nodes:

```
step:...match:12 → dec:14 → dec:16 → step:18 → dec:19   (+ 3 outcome nodes)
```

Sorted, that is `dec:14, dec:16, dec:19, out:14:0, out:16:0, out:19:0, step:12, step:18` — exactly
the 8 reported. Every node has correct in/out edges and correct `containers`. Nothing links the
island to any of the 29 entries.

`DecisionSeeder` exists to anchor precisely this, and skips it —
`services/analysis/decision_seeder.py:40-41`:

```python
if f"dec:{site_id}" in acc.nodes():
    continue
```

**It treats "the node already exists" as "the node is connected."** When a function is summarized,
`DecisionProjector` creates its decision nodes; the seeder then skips them and the island is never
anchored. Existence is not reachability.

**Why it is judge-dependent:** under `HeuristicDecisionJudge` those forks are classified
guard/noise, no `dec:` nodes are created, and no island forms. Under `LlmDecisionJudge` they are
decisions, the projector materialises them, and the seeder skips them. PBI 63 wired the LLM judge
into the served `/trace` path (`dependencies.py`), which is what put this in front of users.

## 3. The design flaw to fix, not just the symptom

`budget_invariants.py:42-45` asserts I2 (total reachability). **No stage establishes it.** An
invariant that is asserted but never established is a crash waiting for the right input.

Add the stage that establishes it, and keep the assert as the check that it worked.

### 3a. Extract the anchoring ladder

`DecisionSeeder._seed_one` (`decision_seeder.py:52-84`) already implements the correct strategy
ladder:

1. nearest call-graph ancestor already in the graph (`_nearest_ancestor`)
2. a sibling node in the same code component (`_component_host`)
3. a synthetic `entry:seed:<component>` anchor (`_anchor_for`)

Extract that ladder into its own injectable collaborator — `services/analysis/anchor_resolver.py`,
class `AnchorResolver` — and have `DecisionSeeder` depend on it rather than own it. Two callers
need this logic; duplicating it guarantees they drift. Keep `DecisionSeeder`'s public behaviour
identical.

### 3b. New pass: `IslandAnchor`

`services/analysis/island_anchor.py`. Runs at the **end of condensation**, on the completed
accumulator, before the graph is handed on:

- Compute the set reachable from all entry nodes.
- Group the unreachable remainder into weakly-connected components.
- For each component, pick its head deterministically: the member with no in-edge from inside the
  component; ties and the no-candidate case (a cycle) break on `(file, line, id)` from `refs`.
- Anchor that head via `AnchorResolver`, exactly as `DecisionSeeder` would.

Sort every iteration. Two runs must produce byte-identical output.

**Do not prune.** `BudgetWorkGraph.prune_unreachable()` exists; do not reach for it. CLAUDE.md:
detail is demoted, never deleted. Code that nothing calls is a real and useful thing to show
anchored under its own seed entry — silently dropping ten decisions is a worse outcome than the
crash.

### 3c. Leave `DecisionSeeder`'s skip condition alone

Do not change `decision_seeder.py:40-41`. Its job is attaching decisions that were never projected;
`IslandAnchor` is now the closing guarantee. Separating those two responsibilities is the point —
resist folding them together.

### 3d. Check whether budgeting can also produce an island

`VisibilityBudgeter` merges and removes nodes after condensation (`recondense`, `fold`, `cap`), so
it could in principle strand a cluster that was reachable before. Anchoring at end of condensation
does not cover that.

**Investigate and report; do not speculatively add a second pass.** Instrument the budgeter to
report whether any island exists immediately before `self._checker.enforce(work)` on both repos.
If none does, say so with the numbers and leave it. If one does, report it — a second anchoring
point inside the budgeter is then a follow-up PBI, not a silent addition here.

## 4. Fix the self-check harness

`scripts/selfrun.py`'s `read_sources()` reads only `agents/`, `shared/` and `api/`. It **excludes
`scripts/`**, so it analyses a smaller slice of CodeFlow than `render_repo.py .` does — which is
exactly why it stayed green while the real entry point crashed on the same repo.

Change `read_sources()` to use `read_python_sources(ROOT)` from `render_repo.py`, the same function
every other script uses. Expect the node/edge counts in selfrun's assertions to move; report the
before/after. **Do not adjust an assertion's threshold to accommodate the new file set without
saying so explicitly and justifying it.**

## 5. Out of scope

- Do not touch naming, review, prompts, geometry or the frontend.
- Do not weaken, loosen or delete `_assert_reachable` or any other invariant. Making the assert
  pass by making the property true is the whole task; making it pass any other way is a fail.
- Do not revert PBI 63's `judge=` wiring in `dependencies.py`. The LLM judge on the served path is
  intended; the crash it exposed is what you are fixing.

## 6. Two pre-existing reds — do not fix, do not hide

`scripts/selfrun.py` currently exits 1 with two explained failures:

- `[FAIL] no guard-selector decision survives: 1 guard decisions` — pre-existing, unrelated.
- `[FAIL] >=4 stitch edges api->agent entries: 3 stitches` — a correct consequence of PBI 64
  retiring the layout-agent call. Its revision is a pending user decision.

Both must remain exactly as they are. If §4's file-set change alters either, report it rather than
adjusting the check.

## 7. Verification

```bash
cd /Users/cooperkeenan/GitHub/CodeFlow && source venv/bin/activate

# The reproduction — must go from crash to clean
python scripts/render_repo.py . /tmp/p66_cf
python scripts/render_repo.py . /tmp/p66_cf2
diff /tmp/p66_cf/flow_graph.json /tmp/p66_cf2/flow_graph.json     # MUST be empty
python scripts/flow_metrics.py /tmp/p66_cf                         # MUST exit 0

# Must not regress the demo target
export REPO=/Users/cooperkeenan/github/django-helpdesk
python scripts/render_repo.py $REPO /tmp/p66_hd
python scripts/render_repo.py $REPO /tmp/p66_hd2
diff /tmp/p66_hd/flow_graph.json /tmp/p66_hd2/flow_graph.json      # MUST be empty
diff /tmp/p66_hd/rendered_view.json /tmp/p66_hd2/rendered_view.json # MUST be empty
python scripts/flow_metrics.py /tmp/p66_hd                          # MUST exit 0, OVERLAPS 0

python scripts/selfrun.py
python scripts/screenshot_flow.py --save cooperkeenan $REPO
python scripts/flow_agent.py $REPO --rebuild state overlaps         # OVERLAPS must be 0
```

Also run the served path, since that is where the report came from — start the tracer agent and
`POST /trace` against a repo, confirming a 200 rather than a 500.

Then **open `scratch_out/flow.png` with the Read tool and look at it.** Anchoring adds synthetic
entries; confirm they read sensibly and have not made the top level worse. The skeleton is
currently 16 nodes against a budget of 15 — report the number after your change.

**Evidence discipline**: every number must come from a command whose artifacts still exist on disk
when you finish. Do not delete verification directories. Quote real output.

## 8. Acceptance

- `python scripts/render_repo.py . /tmp/p66_cf` **completes** — the CodeFlow reproduction is gone.
- Determinism holds on both repos, both files.
- `flow_metrics.py` exits 0 on both repos with roots 1, I5 0, I2 0, OVERLAPS 0.
- django-helpdesk node/edge counts are unchanged at **394 / 488** — this PBI must not alter a graph
  that was already reachable. If they move, explain exactly why.
- `_assert_reachable` is untouched and passing.
- `selfrun.py` analyses the same file set as `render_repo.py .`; the two pre-existing reds are
  still the only reds.
- A report on §3d: does budgeting strand anything, yes or no, with numbers.
- Every file touched ≤ 150 lines.
