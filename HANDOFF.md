# Handoff — Decision-tree diagram, current state

Read this first. It describes what the pipeline does today, how to verify a change, and every
known open defect — not the history of how it got here.

Branch: `featue/isolate`.

---

## 1. What this is

CodeFlow turns a Python codebase into a **decision diagram**: static analysis finds every point
the code branches, an LLM judges which forks are decisions a human would actually reason about,
and the result renders as a tree with `file:line` provenance on every node. Static analysis owns
structure; the LLM only judges significance and writes labels — it may never add, remove, merge or
rewire a node or edge.

The diagram uses **progressive disclosure**: one always-visible high-level view (max 15 nodes, see
`CLAUDE.md`), with a `+` per branch that reveals the decisions and outcomes nested underneath.
Nothing is deleted to fit the page — detail is demoted to a deeper `level` and reached by expanding.

## 2. The containment model

Every `FlowNode` (`shared/models/flow_graph.py`) carries:

- `containers: list[str]` — the node's parent(s) in the containment tree. A node with no
  containers is a root (there must be exactly one: `root:<repo>`).
- `level: int` — containment depth from a root/skeleton node, computed by BFS over `containers`
  (`ContainmentIndexer._assign_levels`). `0` = always drawn (skeleton); `1+` = revealed by a
  parent's `+`.
- `hidden_children: list[str]` — the node's immediate members, topologically sorted. This is
  exactly what a `+` reveals.
- `body_kind: "flow" | "list"` — whether the members read as one sequential thing or a set of
  mutually exclusive/parallel alternatives. Drives whether the renderer chains them or lays them
  out as a set.
- `body_head: str`, `body_tails: list[str]` — for a `"flow"` body, the single entry member and the
  member(s) with no internal successor. Empty/`""` for `"list"` bodies.

`ContainmentIndexer` (`services/analysis/containment_indexer.py`) computes all of this from
`containers` + the edge set, in two passes: `_assign_shape` (topo-sorts members, finds tails),
then `_assign_kind` (decides `flow` vs `list` — see I3 below).

### I3 is a derivation rule, not an assert

A `"flow"` body is supposed to have a single entry point reachable only from its owner or from
inside the body itself. **This is enforced by computing `body_kind` from the property, not by
asserting the property holds.** If a member has no in-edge from the owner or the rest of the body
(`headless`), or the body isn't cohesive, `_assign_kind` classifies it `"list"` instead of raising.

This was tried the other way — asserting single-entry as invariant I3 — and it **crashed the
pipeline on CodeFlow's own repo**: a shared, memoized node can legitimately be both the
predecessor of a body member *and* a containment ancestor of that body reached by a different
path, so "single entry" is sometimes structurally false without being a bug. `scripts/flow_metrics.py`
prints the I3 count (`flow bodies clean`) for visibility, but it is informational only — it is
**not** in the script's exit-code condition. Do not add an assert back for this.

**I1 (DAG), I2 (total reachability from the root) and I5 (cohesion) ARE hard asserts** —
`ContainmentInvariants.enforce_structure` / `enforce_bodies` in
`services/analysis/containment_invariants.py`, called from `BudgetInvariantChecker`. Those three
really do hold unconditionally; only I3 is a soft derivation.

### The flow/list ratio is not a quality metric

A decision's arms are **mutually exclusive alternatives** — that is what a decision *is* — so a
fork is correctly classified `body_kind == "list"`, not a defect to chase down. A falling
flow/list ratio is not a regression by itself. `scripts/flow_metrics.py` reports forks and sequence
bodies **separately** for exactly this reason:

```
decision forks  26  (0 fork only to outcomes)
sequence bodies 68  (18 are chains)
```

Judge those two numbers independently. If you need to know whether disclosure is getting better or
worse, open the PNG — see `CLAUDE.md`'s "Always Run It And Look At The Picture".

## 3. The pipeline

Composed by `services/analysis/flow_pipeline.py`; see `PROMPT.md` for the stage list. The two
services worth understanding beyond the primer:

- **`FlowCondenser`** — indexes the repo, resolves calls, extracts forks, judges them via the LLM,
  and projects the result onto a `FlowGraph` of `entry`/`step`/`decision`/`parallel`/`effect`/
  `outcome` nodes. `DecisionProjector` emits the `decision` node and, for arms that terminate
  without reaching further code, an `outcome` node (`OutcomeLabeler` names it: `Returns`, `Raises`,
  `Continues`, or a verdict-supplied label). `StepMerger` then collapses straight-line single-
  successor step chains.
- **`VisibilityBudgeter`** — replaces the old destructive `PageBudgeter`. Nothing is deleted:
  `BudgetRecondenser` / `ArmFolder` / `EffectCapper` collapse mergeable nodes, `SequenceChainer`
  links same-owner body members into a `sequence` edge where safe, `ContainmentIndexer` computes
  containment shape, `SkeletonReducer` **demotes** low-ranked nodes to a deeper `level` rather than
  removing them, and `SkeletonProjector` / `RevealChunker` prepare what each `+` will reveal.

`ContainerRepointer` (`services/analysis/container_repointer.py`) is the shared collaborator behind
every merge/absorb operation across `BudgetRecondenser`, `EffectCapper` and `StepMerger`: when two
nodes merge, it re-parents every node that contained the removed one onto the survivor, and refuses
to introduce a containment cycle. It depends only on a minimal `id -> object with .containers`
mapping — not on `BudgetWorkGraph` — so it works identically whether the caller holds
`BudgetWorkGraph.nodes` or `StepMerger`'s plain draft dict.

## 4. Verification

```bash
cd /Users/cooperkeenan/GitHub/CodeFlow && source venv/bin/activate

python scripts/render_repo.py /Users/cooperkeenan/github/django-helpdesk /tmp/hd
python scripts/render_repo.py /Users/cooperkeenan/github/django-helpdesk /tmp/hd2
diff /tmp/hd/flow_graph.json /tmp/hd2/flow_graph.json      # must be empty — determinism

python scripts/flow_metrics.py /tmp/hd                      # must exit 0 — see below
python scripts/selfrun.py                                   # 5 assertions, 4/5 is expected (see §6)
python scripts/screenshot_flow.py --save cooperkeenan <repo>  # then Read scratch_out/flow.png
```

`scripts/flow_metrics.py <out_dir>` is the standard structural verification harness — run it
alongside `screenshot_flow.py` and `flow_agent.py`, not instead of them. It exits 0 only when
containment is a single-rooted DAG (I1/I2), cohesion holds (I5) and the rendered view has zero
overlapping node boxes. It prints, but does not fail on: the I3 single-entry count, the fork/chain
split, and body size distribution — those are context for a human reading the run, not pass/fail
gates. See §2 above for why.

For frontend work, `/flow-fixture` renders the real `FlowPage` against
`frontend/public/fixture/rendered_view.json` with no API, DB or login.

## 5. The editable-diagram slice — built, not wired

`api/routers/diagram_edits.py`, `api/services/diagram_edit_service.py`,
`api/models/diagram_edit_model.py`, `shared/diagram_edit_store/` (protocol + Neon implementation),
and on the frontend `frontend/src/hooks/useDiagramEdits.js`,
`frontend/src/hooks/graph/applyEdits.js`, `frontend/src/api/diagrams.js`, and
`frontend/src/components/diagram/edit/{EditToolbar.jsx,useEditableCanvas.js,edgeMarkers.js}` — a
draw.io-style edit-mode overlay that diffs against the rendered view and persists edits — are all
built and untouched by this refactor.

**This is currently unreachable, on purpose**: `diagram_edits.py` is not mounted in `api/main.py`,
and no page imports `EditToolbar` or `useEditableCanvas`. This is not dead code to delete — the
user has decided to wire it up in a later PBI. Leave it alone until that PBI exists.

## 6. Honest open defects

Real numbers, not rounded for effect:

- **Top level is 18 nodes with essentially one edge between them.** This is the biggest visible
  weakness. The skeleton is component-shaped, but seed anchors are roots by definition, so most of
  the top-level nodes sit on one row unconnected to each other. Connecting them is a *structural*
  problem — the underlying call graph genuinely has few edges between top-level components, not a
  layout bug.
- **`PillarGatewaySelector` scores `entry:group:*` route groups 0** because its scoring reads
  `node.backing` (`pillar_gateway_selector.py:13`) and route-group entries carry no `backing` —
  they're aggregates, not single functions. They lose skeleton slots to less central
  `entry:seed:*` anchors that do have backing. Needs a scoring path that doesn't require `backing`
  to be non-empty.
- **Chunked bodies can be `body_kind == "flow"` with `body_head == None`** (one case measured on
  django-helpdesk). When this happens it silently disables the chain re-routing that
  `SequenceChainer` depends on for that body — the body still renders, just not as a chain. Not
  yet root-caused.
- **Single-path decisions render as a command shape but are still labelled as a question.**
  `flow_node_treatment.shape_for` draws a decision with exactly one live arm as `"pipeline"`/`"rect"`
  (a step, not a diamond) via `is_linear`, but the label text still comes from `DecisionLabeler`,
  which always phrases a decision as a question regardless of arm count. Fixing the label needs a
  `decision_judge_prompt.py` change and a `PROMPT_VERSION` bump, or the verdict cache will keep
  serving the old phrasing.
- **`sequence bodies`: only 5 of 33 form chains on django-helpdesk, 18 of 69 on CodeFlow.**
  `SequenceChainer` only links same-owner, single-arm-edge, same-`owner_fqn` members — most
  sequence-shaped bodies don't meet all three conditions, so they render as an unordered set even
  though they are, structurally, a `"flow"` body. This is the same shape as the flow/list point in
  §2: not every `"flow"` body is a chain, and that's fine — chaining a body that fails the
  conditions would fabricate an edge that isn't real.

## 7. Constraints

`CLAUDE.md` is law: ≤150 lines per file, one class per file, constructor injection, type
annotations, no docstrings or explanatory comments, no unsolicited tests, no hardcoding this repo's
own layout, determinism, static analysis owns structure, never weaken a check to go green. Read it
in full before touching the pipeline.
