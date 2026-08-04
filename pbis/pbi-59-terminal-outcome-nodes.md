# PBI 59 — Terminal outcome nodes (every decision leads somewhere)

**Model: implement with Sonnet.**
**Frontend changes ARE authorized for this PBI** (a new node kind must be renderable) — but only the
files named in §6. Nothing else under `frontend/`.
**Depends on PBI 58.**

## Why

The user's mockup is built on two-armed forks: a decision with one arm to each outcome. Measured on
`django-helpdesk`:

| | |
|---|---|
| Decisions | 222 |
| Decisions with **zero** arm edges | **171** |
| Decisions with one arm | 48 |
| Decisions with two arms | **3** |
| Decisions with zero outgoing edges of any kind | **69** |
| Nodes badged `guarded` | 86 (77 decisions) |

So a fork almost never shows both branches. The mechanism is `function_projector.py:124-128`:

```python
if ahead is None:
    if arm.terminal == "falls_through":
        tails.append(node_id)
    else:
        self._acc.add_badge(node_id, "guarded")
```

An arm whose body is just `return HttpResponseForbidden()` produces no `FlowEvent` — the callee is
not a project function and raises no `EffectSite` — so `ahead is None`, so **the arm emits no node
and no edge**. Static analysis found a terminal arm and then threw the structure away.

The consequence is that boxes dead-end: 69 decisions lead nowhere, so a revealed sub-flow has no
exit to draw a line from. HANDOFF §11 identified terminal outcome nodes as the prerequisite for the
box work, and this is it.

**This does not violate "static analysis owns structure."** `terminal_classifier.classify_terminal`
is a pure AST walk over `ast.Return` / `ast.Raise` / `ast.Continue`. The node's existence, id, kind
and edge are all decided by that walk. The LLM contributes at most a human-readable label to an arm
that already exists — it relabels, it does not create.

## Scope

### 1. Model

`shared/models/flow_graph.py`:

```python
NodeKind = Literal["entry", "step", "decision", "parallel", "effect", "outcome"]
```

`shared/models/node_geometry.py` — register an `"outcome"` shape in `NODE_GEOMETRY`. `geometry_for`
raises on an unknown shape rather than defaulting (that is deliberate — silent defaults are how the
three-size-model drift in HANDOFF §7 happened), so a missing entry will fail loudly. Good.

### 2. Emission — the decision branch of `FunctionProjector`

Replace the badge-only path. When `ahead is None` and
`arm.terminal in {"returns", "raises", "continues"}`:

- create node `out:<site.id>:<arm.index>`, kind `"outcome"`
- `refs=[site.span]` so provenance holds (`PROMPT.md` promises provenance on every node)
- `containers=[f"dec:{site.id}"]`, `owner_fqn=fqn`, `arm_path = prefix + [f"{site.id}#{arm.index}"]`
  (PBI 57's fields — the outcome lives inside the decision's body)
- connect `dec:<site.id> → out:<site.id>:<arm.index>` with `kind="arm"`,
  `arm_label` from the labeler below, `group_id=site.id`

`falls_through` keeps its current behaviour exactly — it appends to `tails` and emits nothing.

**Keep the `guarded` badge.** Dropping it would silently change the badge population and the legend
for reasons unrelated to this PBI.

### 3. New — `services/analysis/outcome_labeler.py`

```python
class OutcomeLabeler:
    def label(self, arm: Arm, verdict: SiteVerdict | None) -> str: ...
```

Precedence, highest first:

1. `verdict.arm_labels[arm.index]` when present and non-empty — the LLM's wording for that arm
2. `arm.label_source` when non-empty
3. a fixed word from `arm.terminal`: `returns` → `"Returns"`, `raises` → `"Raises"`,
   `continues` → `"Continues"`

No new prompt, no new LLM call, so **do not bump `PROMPT_VERSION`**.

### 4. Invariant I7 — `containment_invariants.py`

```
I7  termination   every decision node has out-degree >= 1
```

There are **69 violations before this PBI**. Add I7 as part of this PBI, once the emission above
makes it true. If it does not go to zero, report the remaining violators with their ids and
`arm.terminal` values — do **not** soften the invariant to accommodate them.

### 5. Shape — `agents/render_agent/placement/flow_node_treatment.py`

`shape_for` must return `"outcome"` for the new kind. Outcome nodes are **not expandable** — they
have no body.

### 6. Frontend (authorized, these files only)

- new `frontend/src/components/flow/nodes/OutcomeNode.jsx` — route through `NodeChrome` like
  `EffectNode` does, so the one component keeps owning label clamping, badges and chrome. Grey
  rounded rect, no expand affordance.
- `frontend/src/components/flow/FlowCanvas.jsx` — add `outcome: OutcomeNode` to `NODE_TYPES`.
- `frontend/src/components/flow/styles.js` — add `KIND_ACCENT.outcome`.
- `frontend/src/components/flow/Legend.jsx` — one legend row.

Do not touch `useExpansion.js`, `expansionBoxes.js`, `GroupBox.jsx`, `useGraphTransform.js` or
anything else. Box and edge work is a later PBI.

## Acceptance

```bash
cd /Users/cooperkeenan/GitHub/CodeFlow && source venv/bin/activate
HD=/Users/cooperkeenan/github/django-helpdesk
python scripts/render_repo.py $HD /tmp/hd && python scripts/render_repo.py $HD /tmp/hd2
diff /tmp/hd/flow_graph.json /tmp/hd2/flow_graph.json     # MUST be empty
python scripts/selfrun.py                                  # >= 4/5
python scripts/flow_agent.py $HD --rebuild state overlaps  # OVERLAPS: 0
```

```bash
python - <<'PY'
import json, collections
g = json.load(open('/tmp/hd/flow_graph.json'))
out = collections.Counter()
for e in g['edges']:
    out[e['source']] += 1
d = [x for x in g['nodes'] if x['kind'] == 'decision']
print('decisions:', len(d), ' with 0 out-edges:', sum(1 for x in d if out[x['id']] == 0))
print('outcome nodes:', sum(1 for x in g['nodes'] if x['kind'] == 'outcome'))
print('total nodes:', len(g['nodes']), ' total edges:', len(g['edges']))
print('arm edges:', sum(1 for e in g['edges'] if e['kind'] == 'arm'))
gid = collections.Counter(e['group_id'] for e in g['edges'] if e['kind'] == 'arm')
print('arms per group:', dict(sorted(collections.Counter(gid.values()).items())))
PY
```

Required:

1. **`with 0 out-edges` goes 69 → 0.**
2. `arm edges` rises materially from **54**; `arms per group` shows far more 2-arm groups than
   today's **3**.
3. `outcome nodes` — **report the honest count.** ~250 is expected. If it comes out much larger,
   say so and propose deduping to `out:<owner_fqn>:<terminal>` as a follow-up. Do **not** silently
   cap or merge to keep the number pretty.
4. `diff` byte-empty; `OVERLAPS: 0`.

Then look at the picture:

```bash
python scripts/screenshot_flow.py --save cooperkeenan $HD
python scripts/flow_agent.py $HD "toggle:<a decision id with 2 arms>" state overlaps \
    "shot:scratch_out/d1.png"
```

Open both PNGs **with the Read tool and actually look at them**. A decision should now visibly fork
to two outcomes, as in the mockup. Counts are not evidence.

## Constraints

`CLAUDE.md` is law: ≤150 lines per file, one class per file, constructor injection, type annotations
on all signatures, no docstrings or explanatory comments, no unsolicited tests, no unused imports.

Determinism: byte-identical `flow_graph.json` across two runs; sort every set/dict iteration.

No prompt changes → **no `PROMPT_VERSION` bump**. No new LLM calls.

`selfrun.py` is 4/5 with one deliberate red (*no guard-selector decision survives*). Outcome nodes
will not change it. Leave it failing; do not tune the regex.

**Never weaken an assertion, invariant or budget to make a run pass.** If I7 will not reach zero,
report the real violators and stop — a red assertion is information.
