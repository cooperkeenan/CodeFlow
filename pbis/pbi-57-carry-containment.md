# PBI 57 — Carry containment metadata (`owner_fqn`, `arm_path`, `containers`)

**Model: implement with Sonnet.** Backend only — do not touch `frontend/`.
**Metadata only. This PBI must produce zero visual change.**

## Why

Clicking `+` today dumps a flat fan of unrelated decisions. Measured on `django-helpdesk`
(`/tmp/hd/flow_graph.json`, 283 nodes / 399 edges):

| | |
|---|---|
| Edges between the direct `hidden_children` of any skeleton node | **0** — all 15 reveals are pure stars |
| Reachability overlap between reveal "regions" | Jaccard **0.99** |
| Same-owner-function edges that exist but are never revealed | **108** across 132 owner functions |

Root cause: `function_projector.py:77` calls `chain.splice(summary.head, summary.tails, badges)`,
which **inlines every callee's body into its caller's chain**. The FlowGraph is a fully-inlined
control-flow graph with no call boundaries left. So `skeleton_projector.py:43` asking for "immediate
successors of N" returns N's own forks mixed with forks from arbitrarily deep callees.

`_build_region(self, fqn, events, prefix, lane)` **knows** the owning function and the arm path of
every node it creates. `_acc.upsert(...)` at line 118 discards both. This PBI records them.

PBI 58 then derives `hidden_children` from containment instead of graph adjacency. **This PBI
changes nothing that is drawn** — it only adds fields.

## Scope

### 1. Model — `shared/models/flow_graph.py`

```python
class FlowNode(BaseModel):
    ...
    owner_fqn: str = ""
    arm_path: list[str] = []
    containers: list[str] = []
```

- `owner_fqn` — the FQN of the function whose body created this node.
- `arm_path` — `["<site_id>#<arm_index>", ...]`, outermost first. The second containment axis: a
  decision contains its arms. This is **not** recoverable from node ids, which is why it must be
  recorded rather than parsed back out later.
- `containers` — the ids of every node whose body this node belongs to. `[]` means forest root.

`containers` is a **list, not a single value**, and that is deliberate: shared helpers duplicate
under each caller (product decision, this session). `ticket_perm_check` is called from many staff
views and will carry a container for each. Do **not** implement "lowest key wins" / single-home.

Leave `_sort_canonical`'s sort keys alone. Sort `containers` and `arm_path` deterministically before
they reach the model (see §5).

### 2. `GraphAccumulator` — `graph_accumulator.py` (currently 133/150, **must be split**)

Move `_NodeDraft` and `_EdgeDraft` into a new `services/analysis/graph_drafts.py`. Add the three
fields to `_NodeDraft` and two methods:

```python
def set_owner(self, node_id: str, owner_fqn: str, arm_path: list[str]) -> None:
    draft = self._nodes.get(node_id)
    if draft is None or draft.owner_fqn:
        return
    draft.owner_fqn = owner_fqn
    draft.arm_path = list(arm_path)


def add_container(self, node_id: str, container: str) -> None:
    draft = self._nodes.get(node_id)
    if draft is None or node_id == container:
        return
    if container not in draft.containers:
        draft.containers.append(container)
```

`set_owner` is **first-writer-wins** — the region that *created* the node owns it. This matters for
a spliced callee head: it is created inside the callee's region and merely *linked* from the
caller's, so its `owner_fqn` must stay the callee's. First-writer-wins matches `upsert`'s existing
semantics for `label`/`kind`, so it introduces no new determinism assumption.

`add_container` is **additive** — that is the duplication mechanism.

Emit all three in `to_flow_nodes()`.

### 3. `ChainBuilder` — `chain_builder.py`

Add `self.members: list[str] = []` and append `node_id` in `_link` (append-if-absent, preserving
first-seen order). Every node linked into this region — including a spliced callee head — is a
member of this region's body. That is exactly what makes the callee's head appear inside its
caller's box.

### 4. `FunctionProjector` — `function_projector.py` (currently 139/150, **must be split**)

Extract the container logic into a new `services/analysis/container_assigner.py`:

```python
class ContainerAssigner:
    def __init__(self, acc: GraphAccumulator) -> None: ...

    def assign(self, chain: ChainBuilder, fqn: str, prefix: _Path) -> None: ...
```

> **CORRECTED 2026-08-04 — read this, the original rule below it was wrong.**
>
> The first version of this rule was *"`prefix` empty → container is `chain.head`"*. It is wrong and
> must not be implemented. `chain.head` is scoped to a **single `_build_region` call**, so a
> function's arm regions and its spliced-in heads never join up. Measured result: 118 roots, 71
> fully-orphaned decisions, and **only 58 of 283 nodes reachable by drilling** from the 15 top-level
> nodes — strictly worse than today. It also produces genuine containment cycles when the first node
> processed is a spliced, memoized head belonging to another function
> (`extract_email_message_content → decodeUnknown → …` on django-helpdesk).
>
> **The corrected rule, validated against the real graph before being written here:**
>
> - node's `arm_path` **non-empty** → container is `f"dec:{<site_id of the last arm_path entry>}"`
>   (a decision contains its arms). Unchanged — this half already works.
> - node's `arm_path` **empty** → container is the head of the node's **own** function:
>   among all nodes sharing that `owner_fqn` with an empty `arm_path`, the head is
>   `min` on `(refs[0].file, refs[0].line, id)`. Every other member gets the head as container;
>   the head itself keeps whatever container its callers already gave it.
>
> Implement this as a **deterministic post-pass over the accumulated graph**, once, after all
> projection is complete — not as in-loop state during `_build_region`. That is what makes it immune
> to the ordering/memoization hazard, so the `native` guard (`chain.head.owner_fqn == fqn`) is no
> longer needed and should be removed.
>
> Measured effect of the correction (function-level grouping vs. the current `chain.head` rule):
>
> | | covered nodes | bodies >1 member | zero internal edges | meet I5 |
> |---|---|---|---|---|
> | current (`chain.head`) | 165 | 36 | **10** | 19 |
> | **corrected (`owner_fqn`)** | **247** | 55 | **1** | **44** |
>
> Coarser grouping (class/module) was also measured and **rejected**: it fattens bodies but collapses
> cohesion (meet-I5 falls to 14 of 27, then 5 of 12). Function-level is the granularity.

~~Original rule (superseded, do not implement):~~

- ~~`prefix` non-empty → container is `f"dec:{prefix[-1][0]}"`~~
- ~~`prefix` empty → container is `chain.head`~~
- ~~`chain.head is None` → nothing to do, return~~

Set `owner_fqn` / `arm_path` at each creation site, derived from that region's `(fqn, prefix)`:

- `_handle_decision` (line 118) — `owner_fqn=fqn`, `arm_path` from `prefix`
- `ChainBuilder.flush` step nodes — `owner_fqn` = the chain's `_owner`
- `_handle_parallel` (line 102) — `owner_fqn=fqn`
- `_attach_effect` — use **`effect.owner`**, not `fqn`. `_boundary_effects` upserts the same
  `effect.id` from multiple callers, so `fqn` would be whichever caller ran first — arbitrary.
  `effect.owner` is exact and order-independent.

### 5. Nodes created outside `FunctionProjector`

Every one of these must get containment or PBI 58's invariants will fail on *them* rather than on
real nodes:

| Site | Container to set |
|---|---|
| `flow_condenser.py:84` — entry → summary head | entry heads get `containers=[entry.id]`; entries themselves stay `[]` (forest roots) |
| `decision_seeder.py` — seeded anchors + their decisions | anchor is a root; seeded decisions get the anchor as container |
| `arm_folder.py:33` — `fold:<node_id>` | inherit the folded decision's container and `owner_fqn` |
| `reveal_chunker.py:39` — `more:<owner>:<i>` | inherit the owner's container and `owner_fqn` |
| `step_merger.py`, `budget_recondenser.py` | when a node is absorbed, the **survivor keeps its own** containment; re-point any container that named the absorbed node at the survivor, so no dangling id survives |

### 6. Determinism

- `containers` and `arm_path` sorted before serialization; `containers` sorted by id.
- No set iteration anywhere in the new code paths — `add_container` uses a list membership test.
- No floats introduced.

## Acceptance

```bash
cd /Users/cooperkeenan/GitHub/CodeFlow && source venv/bin/activate
HD=/Users/cooperkeenan/github/django-helpdesk
python scripts/render_repo.py $HD /tmp/hd && python scripts/render_repo.py $HD /tmp/hd2
diff /tmp/hd/flow_graph.json /tmp/hd2/flow_graph.json     # MUST be empty
python scripts/selfrun.py                                  # >= 4/5 (one deliberate red — see below)
python scripts/flow_agent.py $HD --rebuild state overlaps  # OVERLAPS: 0
```

Then run this and **report the raw output**:

```bash
python - <<'PY'
import json, collections
g = json.load(open('/tmp/hd/flow_graph.json'))
n = {x['id']: x for x in g['nodes']}

bad = [i for i, x in n.items() if i.startswith(('dec:', 'step:'))
       and x['owner_fqn'] != i.split(':', 1)[1].rsplit(':', 1)[0]]
print('owner_fqn mismatch vs id:', len(bad), bad[:5])

dangling = [(i, c) for i, x in n.items() for c in x['containers'] if c not in n]
print('dangling container refs:', len(dangling), dangling[:5])

roots = [i for i, x in n.items() if not x['containers']]
print('roots:', len(roots))

def ancestors(i, seen):
    for c in n[i]['containers']:
        assert c not in seen, f'CYCLE at {i} -> {c}'
        ancestors(c, seen | {c})
for i in n:
    ancestors(i, {i})
print('containment acyclic: OK')

print('nodes with >1 container (duplicated helpers):',
      sum(1 for x in n.values() if len(x['containers']) > 1))
print('container count distribution:',
      dict(sorted(collections.Counter(len(x['containers']) for x in n.values()).items())))
print('nodes with arm_path:', sum(1 for x in n.values() if x['arm_path']))
PY
```

Required:

1. `owner_fqn mismatch vs id` is **0**.
2. `dangling container refs` is **0**.
3. Containment is **acyclic** (the assert does not fire).
4. **Drill-reachability.** Run the block below.

   > **CORRECTED 2026-08-04 — the earlier version of this check was wrong.** It seeded the walk from
   > nodes with `level == 0`. At this stage `level` still means "is not a decision"; it does not
   > become containment depth until PBI 58. Seeding from it measured nothing useful and produced a
   > bogus `ORPHANED = 223`. **Seed the walk from the containment roots** (`containers == []`).
   >
   > Required: `ORPHANED` is **0** — containment must be total. Also report `roots`; the target is
   > **~43**, not 94. 94 means callee bodies are sitting flat at the top level instead of nested
   > inside their callers, which is the whole fractal property (see §4a).

   ```bash
   python - <<'PY'
   import json, collections
   g = json.load(open('/tmp/hd/flow_graph.json'))
   n = {x['id']: x for x in g['nodes']}
   body = collections.defaultdict(list)
   for i, x in n.items():
       for c in x['containers']:
           body[c].append(i)
   roots = sorted(i for i, x in n.items() if not x['containers'])
   seen, q = set(roots), list(roots)
   while q:
       for m in body.get(q.pop(), []):
           if m not in seen:
               seen.add(m); q.append(m)
   print('reachable from containment roots:', len(seen), 'of', len(n))
   print('ORPHANED:', len(n) - len(seen))
   print('roots:', len(roots), dict(collections.Counter(n[i]['kind'] for i in roots)))
   print('bodies owning >1 member:', sum(1 for v in body.values() if len(v) > 1))
   depth = {}
   def d(i):
       if i in depth: return depth[i]
       depth[i] = 0 if not n[i]['containers'] else 1 + min(d(c) for c in n[i]['containers'])
       return depth[i]
   print('max containment depth:', max(d(i) for i in n))
   PY
   ```

### 4a. Call-boundary links — REQUIRED, added 2026-08-04

`owner_fqn` grouping gives structure *within* a function but nothing links a caller to its callee's
body, because `chain.splice` inlines the callee's head and destroys the boundary. `backing` does not
help: `add_backing` is only called when the callee has **no** head (`function_projector.py:75`), so
it records exactly the leaf callees that need no containment — measured, only 1 of 132 group heads
is reachable that way.

Record the boundary **where it is destroyed**. In `_handle_call`, the caller's fqn and the callee's
fqn (`proj[0].fqn`) are both in hand at the `chain.splice(...)` call. Record the pair, then in the
post-pass add `container(head_of(callee_fqn)) += head_of(caller_fqn)`.

Cycle guard, deterministic: process pairs in sorted order; skip any link whose caller head is
already a containment descendant of the callee head. Measured on django-helpdesk: **135 candidate
links, 124 added, 11 skipped as cyclic**, taking roots from 94 → **43** with `ORPHANED` still 0.

### 4b. Synthetic repo root — pulled forward from Stage 7, added 2026-08-04

43 roots cannot be a 15-node top level. Add `root:<repo>` (kind `entry`, no `refs`, `containers=[]`)
and give every other root `containers=[root:<repo>]`. The top level then becomes **just another
body**, which is what makes the diagram fractal all the way up rather than only below the first
click. Its body is capped at the existing `skeleton_budget = 15`; the remaining ~28 go behind
`+N more`, using the machinery that already exists.

After this, `roots` must be exactly **1** and `ORPHANED` must be **0**.

5. **`nodes with >1 container` is > 0** — if it is 0, the duplication mechanism is not working and
   `ChainBuilder.members` is probably not capturing spliced heads. Report the number.
6. `diff` is byte-empty.
7. **`rendered_view.json` is byte-identical to a pre-change run.** Stash a copy before you start.
   `HiddenEmitter` does not emit the new fields, so anything drawn changing means something else
   moved — investigate rather than accept it.

Report items 4, 5 and the container-count distribution as **numbers**, even if they disappoint.
They are the input to PBI 58's design and to the gate after PBI 59.

## Constraints

`CLAUDE.md` is law: ≤150 lines per file (`function_projector.py` and `graph_accumulator.py` are
already at 139 and 133 — **both must be split as part of this PBI**), one class per file,
constructor injection, type annotations on all signatures, no docstrings or explanatory comments,
no unsolicited tests, no unused imports.

Determinism: same repo in → byte-identical `flow_graph.json` out. Sort every set/dict iteration;
break ties on `(file, line, name)`.

No prompt changes, so **do not** bump `PROMPT_VERSION`.

`scripts/selfrun.py` is currently **4/5**. The red one — *no guard-selector decision survives* —
is failing deliberately (it regex-matches `\bnot\b` and catches `'Token valid and not revoked?'`,
which reads like a real decision). **Leave it failing. Do not tune the regex to go green.** If your
change makes a *different* assertion fail, that is a real regression — report it, do not weaken it.
