# PBI 58 — Derive `hidden_children` from containment, not graph adjacency

**Model: implement with Sonnet.** Backend only — do not touch `frontend/`.
**Depends on PBI 57.** This is the payload PBI: where a `+` starts revealing a coherent sub-flow.

## Why

PBI 57 recorded which function body every node lives in. Nothing reads it yet.

`SkeletonProjector._hidden_region` (`skeleton_projector.py:40-48`) still answers "what does `+`
reveal?" with one hop of graph adjacency:

```python
targets = {
    edge.target
    for edge in graph.out_edges(start)
    if edge.target not in skeleton_ids and edge.target != start
}
```

Because the graph is fully inlined (PBI 57 §Why), that set mixes the node's own forks with forks
from arbitrarily deep callees, across all edge kinds, discarding `group_id` and `kind`. Measured
consequence on `django-helpdesk`: **zero** edges exist between the direct `hidden_children` of any
of the 15 skeleton nodes. Every reveal is a star. Meanwhile **108 same-owner-function edges** exist
in the graph and no `+` shows any of them.

A function body is single-entry/single-exit *by construction* — which is exactly the "one line in,
one line out" box the user's mockup requires. `FlowSummary(head, tails)` already computes that port
pair and throws it away after splicing.

## Scope

### 1. Model — `shared/models/flow_graph.py`

```python
BodyKind = Literal["flow", "list"]

class FlowNode(BaseModel):
    ...
    body_kind: BodyKind = "flow"
    body_head: str = ""
    body_tails: list[str] = []
```

These are **derived**, never authored. `containers` (PBI 57) stays the single source of truth for
the hierarchy; `body_*`, `hidden_children` and `level` are computed from it.

### 2. New — `services/analysis/containment_indexer.py`

```python
class ContainmentIndexer:
    def index(self, graph: BudgetWorkGraph) -> None: ...
```

Computes, for every node `N`:

- **`body(N)`** = every node that lists `N` in its `containers`, ordered by a **unique**
  topological sort of the induced subgraph — Kahn's algorithm popping from a ready-set sorted on
  `(file, line, id)`. Not "some" topological order; the same order every run.
- **`hidden_children`** = `body(N)`. Same field name and wire format as today, so `HiddenEmitter`
  and the frontend keep working unchanged through this PBI.
- **`level`** = depth in the containment DAG. `level == 0` ⟺ `containers == []`. For everything
  else, `level = 1 + min(level of containers)` — shallowest wins, computed by BFS from the roots so
  it terminates on a DAG with shared nodes.
- **`body_head`** = the unique member with no in-edge from another member of the same body.
- **`body_kind`** = `"flow"` iff exactly one such member exists, else `"list"`.
- **`body_tails`** = members with an edge leaving the body, plus members with no out-edges at all.

`body_kind` is **derived and never asserted**. `entry:group:src.helpdesk.views.staff` fans to 36
route handlers that are genuinely parallel request flows (HANDOFF §10 rejected chaining them, and
that rejection stands). Such a body legitimately has no unique head — it is a `"list"`. This is not
a way to dodge a failing check: a body that *should* be a flow but comes out `"list"` is exactly the
diagnostic you want, and §Acceptance requires you to report how many there are.

### 3. `VisibilityBudgeter` — `visibility_budgeter.py`

- Call `ContainmentIndexer` where `_mark_levels` runs today.
- **Delete `_mark_levels`** (`visibility_budgeter.py:78-81`). Its rule was
  `node.level = 1 if node.kind == "decision" else 0`; `level` now means containment depth.
- `RevealChunker` still runs after, still chunks oversized bodies behind `more:` nodes, still using
  `max_reveal_per_node`. Importance-ranked capping is PBI 60, not this one.

### 4. `SkeletonProjector` — `skeleton_projector.py`

Delete `_hidden_region` and `_source_order`. Keep `_walk` / `_dfs` / `_rank` and the `hidden_path`
half — `hidden_path` is retired later, not here. `project()` now returns only edges.

### 5. `SkeletonReducer` — `skeleton_reducer.py`

Today it only ever **demotes** (`node.level = 1` at lines 27 and 41) to fit the skeleton budget.
Under containment, every node already has a natural container, so demotion becomes "stop overriding
the natural container" — i.e. clear the root override.

It now also needs the symmetric **promote** path: if the natural root set is smaller than
`skeleton_budget = 15`, clear `containers` on the highest-ranked bodies until the budget is filled.
Rank with the existing `_rank` tuple (`skeleton_reducer.py:95-111`) — do not invent a second ranking.

**If the natural root set comes out very different from 15, report the number — do not force it.**

### 6. New — `services/analysis/containment_invariants.py`

`budget_invariants.py` composes it (that file is 43 lines and would blow the 150-line limit).

Assert:

```
I1  DAG          every id in `containers` exists; the relation is acyclic
I2  total        exactly ONE root (`root:<repo>`, added in PBI 57 §4b) and every node is
                 reachable from it by drilling. Measured after PBI 57: roots == 1,
                 ORPHANED == 0, max containment depth 7.
                 (replaces _assert_revealable, which only required SOME parent)
I3  single entry -- NOT AN ASSERT. See the correction below. This is the DERIVATION RULE for
                 body_kind, plus a reported metric.
I5  cohesion     len(body(N)) == 1, or internal_edges + owner->head edges >= len(body(N))
```

> **CORRECTED AGAIN 2026-08-04 (second correction) — I3 must not be an assert.**
>
> I3 was written as a hard `assert` in the production pipeline. It is **not a universal property**,
> and asserting it makes the pipeline **crash on valid repos** — `selfrun.py` on CodeFlow itself dies
> before reaching its own assertions.
>
> Three independent investigations established why, and the cause is structural, not a data defect:
> a heavily-shared memoized node (`LabelSynthesizer.humanize`, `GitHubClient` effects) can be
> simultaneously (a) the real execution predecessor of a member inside a box, and (b) already a
> containment *ancestor* of that same box via a different caller path. Adding the container that
> would satisfy I3 would close a genuine cycle, so the cycle guard correctly refuses. The guard is
> right; the leftover gap is inherent to shared utilities.
>
> **This is a correction of a mis-specified invariant, not a threshold being loosened to go green.**
> The rule stays exactly as strict; what changes is that a body which fails it is *classified*
> honestly instead of killing the run:
>
> - **Assert** I1 (DAG) and I2 (total reachability). Both held in every round; both are universal.
> - **Derive** `body_kind`: `"flow"` iff every member's in-edges come from the owner or from inside
>   the owner's subtree (transitive closure of its body); otherwise `"list"`.
> - **Report** the flow/list split every run. That ratio is the quality metric for the whole feature —
>   it is strictly more informative than a crash, and it is what the gate reads.
>
> I5 stays a hard assert, scoped to `body_kind == "flow"` as before.
>
> **Do not** use `"list"` as a dumping ground. Before classifying a body `"list"`, the containment
> construction must first try the *nearest non-cyclic ancestor* rather than giving up when the first
> candidate is blocked by the cycle guard. `"list"` is the honest outcome only when no valid
> container exists.
>
> ---
>
> **CORRECTED 2026-08-04 (first correction) — I3 and I5 were defined wrongly in the first draft.** They said "exactly
> one member with no in-edge from another member". That is wrong: **the owner is not a member of its
> own body** (that is what makes the decision straddle the box top in the mockup), so a decision's
> body legitimately has one head *per arm*. Measured against the real PBI-57 graph, the original
> wording classified only **11** bodies as `flow` and dumped 39 into `list` — including
> `update_ticket:254` (14 members, 11 internal edges) and `create_object_from_email_message:593`
> (11 members, 10 internal edges), which are obviously flows with a fork at the top, not lists.
>
> Under the corrected I3, **22 of 49 multi-member bodies pass**. Closing the remaining 27 is the real
> work of this PBI — those are bodies where `owner_fqn` grouping has pulled in members that are not
> connected to the owner's flow at all. Investigate and fix the grouping; do **not** reclassify them
> as `list` to go green. `body_kind == "list"` is reserved for genuinely parallel bodies (route
> groups, the repo root), and §Acceptance requires you to report the flow/list split.
>
> **Measured baseline from PBI 57 to improve on:**
>
> | | |
> |---|---|
> | bodies (owners with ≥1 member) | 131 |
> | body size distribution | `{1:81, 2:18, 3:12, 4:6, 5:4, 6:2, 7:2, 8:1, 9:1, 11:1, 13:1, 14:1, 64:1}` |
> | multi-member bodies | 50 |
> | pass corrected I3 | 22 of 49 (excluding the root) |
> | pass corrected I5 | 26 of 49 |
> | root body size | 64 (32 entries, 25 decisions, 7 steps) — needs the `skeleton_budget = 15` cap |
>
> **R1 is confirmed: 81 of 131 bodies are size 1.** Stage 3's terminal outcome nodes are the mass
> that fixes this (only 23 nodes carry `arm_path` today because 171 decisions have no arm nodes).
> Do not pad bodies to hide it — report the distribution and let the gate decide.

Delete `_assert_revealable`. Keep `_assert_hidden_paths` and `_assert_reachable` unchanged.

**I4 (size cap) and I7 (every decision has out-degree ≥ 1) are deliberately NOT in this PBI.** I4
needs the importance ranking (PBI 60); I7 needs terminal outcome nodes (PBI 59) and has 69
violations today. Adding either now would mean asserting something known-false. Do not add them,
and do not add a weakened version of them.

**I6 (border) is a report, not an assert, in this PBI** — count edges that leave a body from a
non-tail member and print the number. It becomes a hard assert in the frontend box work, where it
governs rendering. It is a *new* check being introduced at the point it applies, not a relaxed one.

### 7. `HiddenEmitter` — `agents/render_agent/placement/hidden_emitter.py`

Line 50: `node.level == 1` → `node.level >= 1`. Containment now nests deeper than one level, and
anything above 1 would silently vanish from the payload.

### 8. `budget_config.py`

Add `max_body: int = 6`. Not enforced here (PBI 60 enforces it); declared now so both PBIs agree on
the number.

## Acceptance

```bash
cd /Users/cooperkeenan/GitHub/CodeFlow && source venv/bin/activate
HD=/Users/cooperkeenan/github/django-helpdesk
python scripts/render_repo.py $HD /tmp/hd && python scripts/render_repo.py $HD /tmp/hd2
diff /tmp/hd/flow_graph.json /tmp/hd2/flow_graph.json     # MUST be empty
python scripts/selfrun.py                                  # >= 4/5
python scripts/flow_agent.py $HD --rebuild state overlaps  # OVERLAPS: 0
```

Then run this and **report the raw output** — these numbers decide whether the whole approach
survives, so do not summarise them away:

```bash
python - <<'PY'
import json, collections
g = json.load(open('/tmp/hd/flow_graph.json'))
n = {x['id']: x for x in g['nodes']}
out = collections.defaultdict(set)
for e in g['edges']:
    out[e['source']].add(e['target'])

flow = lst = 0
sizes = collections.Counter()
viol = []
for i, x in n.items():
    b = x['hidden_children']
    if not b:
        continue
    sizes[len(b)] += 1
    if x['body_kind'] == 'list':
        lst += 1
        continue
    flow += 1
    members = set(b)
    inner = sum(1 for s in b for t in out[s] if t in members)
    if len(b) > 1 and inner < len(b) - 1:
        viol.append((i, len(b), inner))

print('flow bodies:', flow, '  list bodies:', lst)
print('body size distribution:', dict(sorted(sizes.items())))
print('I5 cohesion violations:', len(viol), viol[:5])
print('skeleton (level 0):', sum(1 for x in n.values() if x['level'] == 0))
print('level distribution:', dict(sorted(collections.Counter(x['level'] for x in n.values()).items())))
print('max body:', max(sizes) if sizes else 0)
PY
```

Required:

1. **`I5 cohesion violations` is 0.** Internal edges inside flow bodies go from **0 today** to
   `>= len(body) - 1`. This is the single number that proves the fix.
2. `staff · 36 routes` reveals route-handler heads with `body_kind == "list"` — **not** 8 unrelated
   decisions from 7 different functions. Check it by hand and quote its `hidden_children`.
3. `OVERLAPS: 0`.
4. `diff` byte-empty.
5. **Report the body size distribution verbatim.** If most bodies are size 1–2 the fractal will look
   sparse — that is a known risk (R1) and the gate after PBI 59 exists to catch it. Report the real
   shape; do not pad bodies or tune anything to make the histogram look better.
6. Report `skeleton (level 0)` and whether `SkeletonReducer` had to promote to reach it.

Then look at the picture, which is not optional:

```bash
python scripts/screenshot_flow.py --save cooperkeenan $HD
python scripts/flow_agent.py $HD "toggle:step:src.helpdesk.models.Ticket.send:688" \
    state overlaps "shot:scratch_out/d1.png"
```

Open `scratch_out/flow.png` and `scratch_out/d1.png` **with the Read tool and actually look**. The
reveal must read as a connected chain, not a fan. Counts are not evidence — overlapping nodes,
spaghetti edges and 50-node fans all pass every assertion in this repo.

## Constraints

`CLAUDE.md` is law: ≤150 lines per file, one class per file, constructor injection, type annotations
on all signatures, no docstrings or explanatory comments, no unsolicited tests, no unused imports.

Determinism: byte-identical `flow_graph.json` across two runs. The topological sort must be
**unique**, not merely valid — a ready-set sorted on `(file, line, id)`, not a plain DFS.

No prompt changes, so do not bump `PROMPT_VERSION`.

`selfrun.py` is 4/5 with one deliberate red (*no guard-selector decision survives*). Leave it
failing; do not tune the regex. A *different* assertion failing is a real regression — report it.

**Never weaken an assertion, invariant or budget to make a run pass.** If I5 fails, that is the
approach telling you something — report the numbers and stop, do not relax the invariant.
