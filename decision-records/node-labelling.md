# Node Selection and Labelling

**Status:** accepted
**Recorded against:** commit `94449d21` (2026-09-05) plus the uncommitted cross-link and caching
work on branch `feature/separate-endpoints`. Re-pin this line to the merge commit when the branch
lands.

This record describes how CodeFlow decides *which* nodes appear in a diagram and *what each one
is called*. It exists because that logic is spread across roughly thirty files in three packages
(`tracer/services/analysis/`, `shared/flow_endpoints/`, `render/placement/`) and is easy to drift
without anyone noticing, since there are no unit tests — determinism is the regression check.

---

## 1. The ownership split

Static analysis owns structure. The LLM owns judgement and words.

Concretely, static analysis owns: discovering fork candidates, classifying each arm as live /
guard / void, computing reach, damping utility functions, the numeric heuristic score, the
ranking, the graph construction, and every elision decision. The LLM owns exactly five things
per candidate fork — a ternary verdict (`decision` / `guard` / `noise`), the `question` text, the
`arm_labels`, a `confidence`, and an `importance` — plus, later, node labels and one-liners.

The LLM never adds, removes, merges or rewires a node or an edge. Every node it names already
existed before it was asked. This is the invariant to protect; if a future change lets a model
emit a node id that static analysis did not produce, that change is wrong regardless of how good
the output looks.

---

## 2. The pipeline

`tracer/services/analysis/flow_pipeline.py` — `FlowPipeline.run(repo, files) -> FlowGraph`.
Thirteen stages, announced through `StageReporter`:

| Stage | What it does | Implementation |
| --- | --- | --- |
| `index` | Parse every file into a `ProjectIndex` | `indexing/project_indexer.py::ProjectIndexer` |
| `resolve` | Resolve each call site to target FQNs | `resolve/call_resolver.py::CallResolver` |
| `forks` | Extract fork candidates (`DispatchSite`) | `forks/dispatch_extractor.py::DispatchExtractor` |
| `effects` | Detect side effects (db, http, llm, file, queue, email, response) | `effects/effect_detector.py::EffectDetector` |
| `judge` | **Selection** — classify each site `decision` / `guarded_step` / `noise` | `significance/significance_filter.py::SignificanceFilter` |
| `condense` | Build the first `FlowGraph` | `condense/flow_condenser.py::FlowCondenser` |
| `entries` | Find route and service entry points | `routes/entry_finder.py::EntryFinder` |
| `stitch` | Add cross-service edges from outbound HTTP to entries | `stitch/flow_stitcher.py::FlowStitcher` |
| `rank` | HITS-style pillar scores per component | `ranking/pillar_ranker.py::PillarRanker` |
| `budget` | Folding, capping, skeleton selection, chunking, containment | `budget/visibility_budgeter.py::VisibilityBudgeter` |
| `name` | **Labelling pass 1** | `labelling/flow_namer.py::FlowNamer` |
| `review` | **Labelling pass 2** — dedupe, page title, lane titles | `labelling/flow_reviewer.py::FlowReviewer` |
| `symbols` | Build `meta["symbol_context"]` | `symbols/symbol_context_builder.py::SymbolContextBuilder` |

Endpoint slicing is deliberately *not* in this list. It runs later, at read time, in the gateway
(`api/gateway/services/endpoint_view_service.py`) — see section 6.

---

## 3. Finding fork candidates

`forks/factory.py::build_dispatch_extractor` composes seven detectors, run in a fixed order:
`BranchDetector` (if-chains, with `elif` flattened into arms, plus ternaries containing a call),
`MatchDetector`, `ExceptDetector`, `TableDetector` (module-level dict literals used as dispatch
tables), `RouteDetector` (delegating to the FastAPI and Django scanners), `PolymorphicDetector`
(any call site resolving to two or more targets, one arm per implementation), and
`DynamicDetector` (`getattr` with a non-constant attribute name).

Each emits a `DispatchSite` keyed `"{owner}:{lineno}"`, carrying its `selector_source`,
`selector_reads`, arms, whether the branches reconverge, and a source span. When an if-chain has
no `else`, a synthetic else arm is added with `terminal="falls_through"` so the arm count reflects
the real branching. Selector text is truncated to 120 characters.

The important property is breadth: this stage does not try to be clever about which forks matter.
It finds everything that could conceivably be a decision and hands the judgement downstream. Do
not add taste to the detectors.

---

## 4. Deciding which forks survive

`significance/significance_filter.py::SignificanceFilter.run` computes utilities, builds the call
graph and its SCC index, computes reach, scores each site, builds a candidate per site, and then
delegates the verdict to a pluggable `DecisionJudge`.

**Utility damping.** `UtilityDamper` marks a component a utility when its fan-in is at or above
`max(utility_min_fan_in, p90(fan_in))` — that is, `max(8, p90)`. Utilities are subtracted from
every arm's reach, so a branch whose arms merely call widely-used helpers does not look important
just because those helpers are popular.

**Arm classification.** `forks/arm_classifier.py` is the guard selector, and it is three lines
that matter: an arm whose terminal is `raises`, `returns` or `continues` *and* whose reach is at
most `guard_reach_limit` (2) is a **guard**; an arm with no reach at all is **void**; everything
else is **live**. This is what separates "validate and bail out" from "a real branch in the
program's behaviour".

**Scoring.** `site_scorer.py` produces
`3.0·log2(1 + |live reach union|) + 2.0·provenance + 2.0·(0 if it reconverges else 1) + 1.0·(kind is route/table/polymorphic)`.
Provenance is 0 when no selector read intersects the owning function's parameters, 2 when the
owner is route-reachable, 1 otherwise — i.e. a branch on data that came in from a request scores
higher than a branch on a local.

**The verdict.** Two implementations of `DecisionJudge`:

The heuristic judge (`heuristic_decision_judge.py`) treats route, table, polymorphic and dynamic
sites as decisions whenever they have at least two arms. For branch, match and except sites it
requires at least two live arms whose reach sets are *mutually exclusive* — neither a subset of
the other — which is what stops "do a bit more work in one branch" from being presented as a
choice. Exactly one live arm plus at least one guard arm yields `guarded_step`. Everything else
is noise.

The LLM judge (`significance/llm_decision_judge.py`) runs `claude-haiku-4-5` at temperature 0 in
batches of 20, over a source snippet capped at 25 lines. It fingerprints each candidate, serves
what it can from cache, and dedupes identical fingerprints so only one representative of each
group is actually sent. Anything the model omits, or any exception at all, falls back to the
heuristic judge and is **not** cached — a fallback verdict must never be mistaken for a considered
one on the next run. Without an API key, `build_decision_judge` returns the heuristic judge alone.

Decisions are ranked on `(-importance, -score, owner, span.line, site_id)`. `importance` is the
LLM's, so the model influences *ordering and visibility* strongly even though it cannot change
the graph.

Verdicts become nodes in `condense/decision_projector.py` (a `dec:{site_id}` node plus one `arm`
edge per arm; empty non-falls-through arms get a `guarded` badge and an outcome node), and
`condense/decision_seeder.py` pulls high-verdict decisions into the graph even when they are not
reachable from a route entry.

---

## 5. Producing the labels

Labels are deterministic first and improved second. `condense/labels.py` synthesises a label from
the selector source, preferring the LLM's `question` when there is one, and arm labels from
`verdict.arm_labels`, then the arm's own source text, then a terminal word (Returns / Raises /
Continues). This lands in `FlowNode.label`.

`FlowNamer` then writes `llm_label` and `one_liner`. It **never overwrites `label`**, so the
deterministic text always remains available underneath. Each node's context includes its arm
label sources and the deterministic labels of its hidden children, so a node is named with
knowledge of what it contains. `NameValidator` rejects labels over 10 words or one-liners over
120 characters. A decision is told whether it is a real fork (two or more arm label sources); the
prompt requires non-forks to be phrased as an action and never to end in a question mark, which
is why the diagram reads as a mix of statements and genuine questions rather than everything
being a question.

`FlowReviewer` then makes a single pass over the whole graph. Its main job is catching sibling
nodes that ended up with identical labels — an artefact of naming nodes in independent batches —
plus the page title, lane titles, and free-text findings.

`PROMPT_VERSION` at the time of writing: decision judge `"2"`, flow name `"4"`, flow review `"3"`,
stitch judge `"1"`. Each is the *first* component of its fingerprint, so bumping one invalidates
that entire cache. Do not bump one unless you mean to pay for a full re-run.

**Fingerprints** (`analysis/fingerprints.py`) are sha256 over components joined by `\x1f`. They
deliberately exclude node ids and file paths. Two structurally identical forks in different files
therefore share a fingerprint, share one LLM call, and share one cache entry. This is a large cost
saving and a consistency win — the same construct gets the same label everywhere — but it means a
label can never depend on *where* the code lives. If you ever want location-sensitive labels, the
fingerprint must change, and that invalidates the cache.

Caches are flat JSON files under `<repo>/.cache/` via `analysis/json_cache.py::JsonCache`, written
sorted for stable diffs. They key the LLM verdict cache; changing a hashed input causes a cache
miss, a live call, different labels, and a broken golden diff.

---

## 6. Choosing what appears in one endpoint's diagram

`shared/flow_endpoints/` slices a single endpoint out of the whole graph at read time.
`EndpointSubgraph.slice` takes the containment closure from the entry node (via `hidden_children`,
not edges), keeps only intra-slice edges, records which targets fall *outside* the slice, prunes
back edges into a deterministic DAG, and hands the result to `EndpointElider`.

`EndpointElider` (budget 16 nodes, at most 3 passes) runs, in order:

**ChunkDissolver** undoes the whole-repo budget stage's `more:` and `fold:` placeholders — inside
one endpoint there is room to show what they were hiding. **SharedHelperCollapser** folds runs of
nodes belonging to an owner that appears in ten or more endpoints into a single `helper:` node,
on the grounds that a helper used everywhere is not what this endpoint is *about*.
**RunCollapser** folds linear runs of three or more steps into one `run:` node named after the
run's tail, since a straight line of calls carries no branching information.

Then a loop: **IslandDemoter** drops anything unreachable from the root; **FanoutCapper** limits
any parent to five children, demoting the overflow ranked by kind then subtree size (decisions
outrank effects outrank plain steps); **EndpointRanker**, only if still over budget, greedily
picks nodes by BFS distance from the root, then kind, then how *exclusive* the owner is to this
endpoint, keeping the result connected. **LevelAssigner** then hosts every hidden node under a
visible one and decides whether each body is a `flow` or a `list`. **TerminalCloser** closes off
dangling paths. Every pass has a floor of 10 nodes — none of them will strip a diagram to nothing.

Note the direction of the exclusivity tie-break: a node whose owner is used by *fewer* endpoints
is preferred. What is specific to this endpoint is what a reader wants to see; what is shared
everywhere is noise here and is visible in its own right elsewhere.

The budget is **16**, not 50. At 50 a large entry such as a 36-route group rendered 50 nodes across
9540 x 3744 px; `fitView` then zoomed to 0.157 and a 340px node was 53px on screen — unreadable.
At 16 the same entry is 17 nodes, and the rest is demoted behind `+N` controls rather than deleted.
This is the CLAUDE.md "top-level diagram is at most 15 nodes" rule applied to endpoint views.

**`SoleChildPromoter` runs last, and exists because of a frontend rule.** `useExpansion.js`
implicitly expands any node whose hidden-child list has exactly one entry, transitively — a lone
`+1` control is not worth showing. So demoting a node that ends up as its host's only hidden child
achieves nothing: the client reveals it again, and renders it *inside an expansion box*, which adds
roughly 250px of vertical dead space and makes the page worse than if the node had simply stayed
visible. The promoter therefore walks the assigned levels and pulls any sole hidden child back into
`keep`, re-assigning levels until none remain (bounded at 4 rounds). The cost is a few nodes over
budget; the benefit is that no endpoint view renders an auto-revealed expansion box at all. This is
the reason the observed maximum is 19 visible nodes rather than 16.

---

## 7. Terminals and cross-diagram references

`TerminalCloser` closes off any kept node that is not already an outcome, has no hidden children,
and has no kept successor. What it does depends on what was actually cut off, and the three cases
are worth knowing because an earlier version got this badly wrong.

If an external target is itself an entry node, it emits `endlink:<that entry id>` labelled
"Continues in X" — a link to that endpoint's diagram.

If the node has external successors that are not entries, it emits `endcont:<owner_fqn>` labelled
from the first external effect ("Writes to the database", "Calls an external service", …) or, failing
that, `Continues into {that node's label}`. Encoding the target's owner in the id is what lets
`LinkResolver` turn it into a clickable link to that function's own diagram, via `OwnerSubgraph` —
which slices any owner, not only the shared ones, so this needs no relaxation of the
"shared by two or more endpoints" rule that governs ordinary terminals.

If the node has **no external successors anywhere in the graph, it emits nothing at all** and the
node is left as a leaf. This is the case that matters most in practice. The previous version emitted
a node labelled "Continues" here, and on django-helpdesk that produced 31 terminals — every one of
them labelled "Continues", roughly a tenth of every visible node — of which only 4 had any
continuation to describe. For the other 27 the label was not merely vague, it was false: nothing
continued. A leaf that simply ends is honest; a node asserting a continuation that does not exist is
not. When a terminal is skipped it must also not be counted in `close()`'s return value, which drives
the retry loop in `EndpointElider`.

`SharedOwnerIndex` computes the exclusivity map consumed above. `counts()` is now derived from
`owners()`, which keeps the sorted entry ids per owner rather than discarding them — that is what
makes link resolution possible.

## 7a. Link resolution

`LinkResolver` turns those references into clickable links. It runs at read time in the gateway
and returns a `node id -> EndpointLink` map **beside** the rendered view. Nothing is stored on
`FlowNode`, so `flow_graph.json` is untouched and the golden-graph check still passes.

Three rules, in order. An `endlink:` node links to that endpoint's diagram. A `helper:` node
(produced by `SharedHelperCollapser`) links to that owner's diagram. Otherwise, a node links to a
helper diagram only if it is a **visible terminal** — level 0, no visible successors — whose owner
is shared by two or more endpoints.

Two restrictions on that last rule matter, and both were added because the naive version produced
useless links:

*Only visible nodes are considered.* Hidden children are in the sliced graph too, and links
attached to them simply never appear on screen.

*The owner must not already be resident in the view.* If some other visible node with successors
has the same `owner_fqn`, the function is already being shown here, and linking to its own diagram
just reopens what the reader is looking at. Skipping those is what turned 28 mostly-circular links
into 18 that each point somewhere genuinely new — a terminal like "Send ticket notification"
handing off to `Ticket.send`'s own diagram.

Helper diagrams themselves come from `OwnerSubgraph`, which picks the owner's head node (the
member with no predecessor inside the owner group, tie-broken on file, line, id) and reuses
`EndpointSubgraph.slice_root` — the same closure, pruning and elision as an endpoint slice, just
rooted somewhere that is not an entry.

---

## 7b. Vertical stretch

`VerticalStretcher` (render side, applied after placement) exists because `fitView` scales to
whichever axis is tighter. When a tree is much wider than it is tall — some endpoints reach an
aspect near 7 — the fit is width-constrained and the vertical space is simply wasted, while
parent-to-child edges run almost horizontally and become impossible to follow.

It computes the placed bounding box, derives `factor = clamp(aspect / 2.0, 1.0, 1.8)`, and scales
every y and every hidden-child `dy` about the minimum y, rounding to integers so no float noise
reaches the JSON. Because it only ever increases vertical gaps it cannot create overlaps.

Two limits are deliberate. It is a **no-op** whenever the aspect is already at or below 2.0, which
is most views — stretching a diagram that is already height-constrained would directly reduce the
zoom and shrink every node. And the cap is 1.8 rather than 3.0: a 3.0 stretch costs nothing in
zoom, but it spreads a shallow wide tree into enormous sweeping edges over an otherwise empty
canvas, which reads worse than the problem it fixes. This is a case where the metric (aspect ratio
reaching its target) improved while the picture got worse — judge it by opening the PNG.

## 8. Rough edges, recorded so they are not rediscovered

- `SignificanceConfig.reach_max_depth = 6` is defined but never read; `ReachComputer` is
  SCC-memoised and unbounded.
- `EndpointRanker._reachable` takes a `distance` parameter it does not use.
- `VerdictCache` lives in `labelling/` although its only consumer is `significance/`.
- Three separate `_KIND_RANK` dictionaries exist — identical ones in `endpoint_ranker.py` and
  `fanout_capper.py`, and a different one in `budget/skeleton_reducer.py`.
- The endpoint view re-derives its own elision at budget 50, while the whole-repo budget stage
  works to `skeleton_budget = 15` / `node_budget = 40`. These are separate tuning surfaces and
  changing one does not affect the other.
