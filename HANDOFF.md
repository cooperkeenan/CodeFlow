# Handoff — Decision-tree diagram, current state

Read this first. It describes what the pipeline does today, how to verify a change, and every
known open defect — not the history of how it got here.

Branch: `feature/isolate`.

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

# the frame (§5) — settled state, then the round trip
python scripts/flow_agent.py <repo> "toggle:<parent>" "isolate:<child>" isolated dimmed overlaps
python scripts/flow_agent.py <repo> "toggle:<parent>" "isolate:<child>" key:Escape isolated dimmed state
```

Expected for the frame: `fill=78%x78%`, `border=dashed 2px r=4px`, exactly one bright node, and after
Escape the `state` dump identical to the pre-isolate one — that round trip is what proves the whole
transform is non-destructive. **Animation defects do not show up here**; sample per frame with
`requestAnimationFrame` and assert on the trace (see `CLAUDE.md`).

`scripts/flow_metrics.py <out_dir>` is the standard structural verification harness — run it
alongside `screenshot_flow.py` and `flow_agent.py`, not instead of them. It exits 0 only when
containment is a single-rooted DAG (I1/I2), cohesion holds (I5) and the rendered view has zero
overlapping node boxes. It prints, but does not fail on: the I3 single-entry count, the fork/chain
split, and body size distribution — those are context for a human reading the run, not pass/fail
gates. See §2 above for why.

For frontend work, `/flow-fixture` renders the real `FlowPage` against
`frontend/public/fixture/rendered_view.json` with no API, DB or login. It takes `?repo=<name>` so the
frame's content path can be exercised; stub it with Playwright's `page.route("**/explain", ...)`.

## 5. Isolate — the frame

Clicking a revealed node's `isolate` control (`NodeChrome` renders it only when `data.depth > 0`,
i.e. on nodes revealed by a `+`) transforms **that node** into a large rectangle — the **frame** —
rather than opening a side panel. See `PROMPT.md` for the term. The frame shows the node title at
top-centre, then `file:line`, the class or function it resolves to, and its methods and helpers each
with a one-line plain-English summary (`isolate/FrameContent.jsx`, reusing `PrimarySummary`,
`MethodList` and `HelperList`). Content is fetched on demand from `POST /repomaps/{repo}/explain` and
cached server-side by fingerprint — never generated for every node up front.

**Summary lengths live in two places, and the prompt alone is not enough.**
`ExplanationValidator._clamp` truncates by word count and is the real authority — a prompt change
without a matching clamp change is silently discarded. `_MAX_SUMMARY_WORDS` (12) governs method and
helper summaries; `_MAX_PRIMARY_WORDS` (40) governs `primary_summary`, which is deliberately two
sentences so the frame leads with a real description. The heuristic fallback is clamped too: it is
reached per-fqn whenever the LLM omits that key, and unclamped it leaked raw docstring text
(measured: an 18-word summary with an embedded newline) straight into the frame.

Any change to `agents/explain_agent/prompts/explain_prompt.py` needs `PROMPT_VERSION` bumped in
`shared/explain_prompt_version.py` — it feeds `NodeExplainService._fingerprint`, so without the bump
every already-explained node keeps serving the old wording from the `ExplanationStore`.

Method and helper rows come from one `isolate/SymbolList.jsx` (`MethodList`/`HelperList` are thin
wrappers over it), paginated **4** per page with a `‹ 1/2 ›` pager at the right of the heading, shown
only when the list overflows one page. Four is deliberate: summaries wrap rather than truncate, so
the page size is what keeps the list short. Do not re-add `nowrap`/ellipsis to the summary — cutting
descriptions off was the thing being fixed.

While a frame is open the minimap gets `.rf-minimap-behind` (opacity `.22`, `z-index: 0`). React
Flow gives `.react-flow__panel` `z-index: 5` and `.react-flow__renderer` `4`, so dropping the panel
to 0 is what actually puts it behind the frame — dimming alone leaves it floating on top. The legend
(`Legend.jsx`) starts collapsed and is still expandable. Explanations are also cached **client-side** in
`hooks/ExplanationCacheContext.jsx` — a `Map` in a `useRef` behind a provider, not module-level state
— keyed `` `${repo}::${nodeId}` ``, so re-opening a frame issues zero requests and skips the loading
skeleton. Errors are never cached.

The frame's right column has a `‹/›` **code** / `⇄` **sequence** toggle (`isolate/ViewToggle.jsx`).
Code mode shows the selected symbol's source (`isolate/CodeView.jsx`): line-numbered, 10px, filling
the frame's height and scrolling internally. Sequence mode (`isolate/SequenceView.jsx`) shows the
**whole class** — every method with calls, in definition order, each listing its outgoing calls in
source-line order.

Both scroll containers need `className="nowheel"` or the wheel zooms the canvas instead of scrolling.

Scrollbar styling is scoped to `.rf-iso`/`.rf-frame-in` **descendants**, not to one pane. The frame
has several independent scroll containers (left column, right column, code `<pre>`), and styling only
the code pane left the others with the browser default — which flashes white against the dark canvas
during the expand. The right column is also reserved but **empty until `data.frameReady`**, so the
code view mounts once at full size instead of laying itself out repeatedly while the frame grows.

**The sequence data needs a re-analysis to appear.** `CalleeIndex` historically stored callees in a
`set` and returned them alphabetically, discarding call order. It now also exposes
`calls_of(fqn) -> ((line, fqn), ...)` sorted on the compound `(line, fqn)` key — the compound key is
what keeps it deterministic when two calls share a line. `SymbolContextBuilder._function_entry` emits
that as `"calls"` alongside the untouched `"callees"`, and `SymbolContextResolver.sequence_for`
assembles the per-class sequence (dropping `ext:` callees, capped at `_MAX_CALLS_PER_CALLER`).
Because `"calls"` lives in the persisted `symbol_context`, **any repo map analysed before this change
returns `sequence: []`** and the frame says so rather than inventing an order. Re-run the analysis. The source comes from `sources` on the explain response — built in
`NodeExplainService.explain` from the same deterministic slices it already computes, and
deliberately assembled **before** the `ExplanationStore` cache check so a cache hit still returns
fresh code instead of dropping it. Explanations are LLM-generated and cached; source never is.

**The isolated shell needs a definite `height`, not just `minHeight`.** `IsolatedChrome` scales its
content with an absolutely-positioned `transform: scale()` wrapper at `height: 100%`; a percentage
height resolves against `height`, so with only `minHeight` set it computes to `auto` and the whole
frame body collapses to zero and renders blank while the DOM and React state look perfectly correct.
`shellStyle` therefore sets `height: base.minHeight` and `alignItems: 'stretch'` when isolated.

**Frame typography must be scaled by `data.frameScale` (= 1 / frozen zoom).** The frame is sized in
*flow* units, so at a typical fit-view zoom of 0.38 an unscaled 11px font renders at ~4px on screen —
present, correct and unreadable. `IsolatedChrome` scales the title and close control directly and
wraps the body in a `transform: scale(frameScale)` container so the list components need no changes.

The sequence, driven by `hooks/useIsolatedView.js` + `hooks/useIsolateAnimation.js`:

1. **Dim** (`DIM_MS` 160) — every other node/edge gets `.rf-dim`. The isolated node is left pixel-
   identical on purpose; nothing grows yet.
2. **Expand** (`EXPAND_MS` 760, `cubic-bezier(.5,0,.2,1)`) — the node takes its **final** geometry
   immediately and grows via a pure CSS `transform: scale()` keyframe (`.rf-frame-in`, starting from
   the `--rf-k0` custom property = nodeWidth/rectWidth). `shellStyle` therefore drops the
   width/min-height transition while `isolated === 'open'`; only the close path keeps it.
   `isolateLayout.spreadNodes` drifts the other nodes aside, and `CameraController` pans (never
   zooms) to centre it, and **does not move on close**.

   **The box animates its layout size; the content does not re-lay-out.** These pull in opposite
   directions and both matter:
   - Edges only stay attached if React Flow sees the node's real dimensions change, so the shell
     keeps its `width`/`min-height` transition. Scaling the shell instead detaches every edge,
     because handles are placed from the layout box, not the painted one.
   - Text only avoids re-wrapping if its container never changes width, so `IsolatedChrome`'s content
     wrapper is a **fixed pixel width** (`frameWidth / frameScale`) and rides a `transform: scale()`
     keyframe (`.rf-frame-grow`, `--rf-from`/`--rf-to`) on the same 760ms curve as the box.
   Measured: content layout width and row height each hold a single value (1528 / 26) for the whole
   expansion, while the box grows 107→1528 with a max edge-to-box gap of **2px**.

   **The frame's position never changes — `isolateRect` anchors it at the node's own top-left.**
   Centring the rect on the node's centre meant the node's `position` had to move, and React Flow
   recomputes edge geometry from the logical position instantly while CSS slides the box there, so
   every edge pointed at the destination for the whole 760ms. Anchoring at `box.x`/`box.y` means only
   the size animates, which React Flow tracks natively. `.rf-iso` therefore must **not** have a
   `transform` transition (only `.rf-shift`, for the nodes being pushed aside). Measured after:
   max edge-to-box gap **2px** across both open and close, with edges mounted in all but ~3 frames.
   `CameraController` handles the recentring, using `rect.cx`/`rect.cy`.
3. **Dash** at the halfway point — `useIsolateAnimation` flips a flag at `DIM_MS + EXPAND_MS/2`,
   which feeds `shellStyle`'s existing `dashed` flag.

The motion is driven by **CSS transitions**, not per-frame JS. A JS/rAF driver was tried — it makes
React Flow's edge geometry track the node exactly — and was **reverted**: recreating every node
object each frame forces React Flow to re-derive `nodeInternals`, which dropped the canvas from
**61 fps to ~9 fps** (measured, 16 frames in 1.8s vs 109). Do not reintroduce it.

Edges are hidden (`.rf-edge-hide`, opacity 0) for the whole transition and fade back in when it
settles. This is not cosmetic tidying: React Flow **unmounts its entire edge layer** while a node's
dimensions are changing, because `createNodeInternals` rebuilds internals with `{...node}` and loses
the measured `width`/`height` it had written onto the previous node objects. Measured: all 4 edges
absent from the DOM for ~750ms of the growth. Hiding them means that unmount happens at opacity 0
instead of as a flicker; once settled the edges return attached (endpoint-to-node-box gap: 2px).

**On close the frame must shrink *as a frame*, continuously.** Three things have to move together or
the collapse reads as a jump:

- `data.isolated` is `'open' | 'closing'`, not a boolean. `useIsolateAnimation` keeps its `id` through
  the close, and `useIsolatedView`'s `closingId` branch returns the node to its original geometry
  while keeping the frame chrome. `shellStyle` pins `borderRadius: 4` only for `'open'`, so on close
  the radius **animates** to the node's own shape (`border-radius` is in the transition list).
  Without this a single-arm decision snaps to `borderRadius: 999` and shrinks as a stadium.
- The frame's content is one `transform: scale()` wrapper (`IsolatedChrome`), and `closeScale()`
  drops that scale by `nodeWidth / rectWidth` for the close, with the same 760ms easing. Without it
  the text stays at full size inside a shrinking box and **reflows/wraps** on the way down.
- Measured close: width 3998→280 flow units, radius 4px→999px, content scale 2.62→0.11, all in step.
- **The chrome swap happens mid-shrink, not at the end.** `useIsolateAnimation` flips `swapped` at
  `EXPAND_MS * SWAP_AT` (0.62) during the close, and `useIsolatedView`'s `restoringId` branch then
  renders the ordinary node chrome with a short `.rf-swap-in` fade while the box is still moving.
  Measured: the swap lands at 640ms with the box 88% shrunk. Swapping at the *end* instead makes the
  frame visibly pop back into a node; swapping much earlier leaves node chrome stranded in a box
  several times its size. Only the title is shared by both chromes, and it rides the shrinking
  `transform: scale()` wrapper (origin `top left`), so it converges on the node's own label position.

`border-style` is not animatable, so dashed→solid still snaps at the very end. By then the content is
scaled to ~0.1 and the box is at node size, so it is not noticeable; do not spend effort on it.

Five things here are load-bearing and easy to break:

- **The rect is frozen at isolate time.** `isolateRect` divides by zoom to turn "78% of the screen"
  into flow units, but `frozenZoom` captures the zoom once and `zoom` is deliberately *not* a
  dependency of the isolation memo. Put it back in and the node resizes as you zoom.
- **`spreadNodes` cascades; it does not shove uniformly.** Nodes on each side are sorted along the
  push axis and each moves only as far as the one in front of it requires. A uniform per-side push
  empties the canvas (distant nodes get shoved off-screen); pushing each node by just its own
  clearance collapses them onto the boundary. The cascade is the only one of the three that both
  keeps overlaps at 0 and leaves the surrounding graph in view.
- **`FlowPage` ignores `onPaneClick` for `PANE_CLICK_GRACE_MS` after an isolate.** The isolate
  control fires on `pointerdown`; React swaps the button's DOM node before `mouseup`, so the
  browser resolves the `click` target to the nearest common ancestor — the pane — and the pane
  handler would immediately clear the isolation. Remove the grace window and isolate stops working
  entirely for a real mouse click.

Everything in `components/flow/isolate/` is live and rendered. `IsolatePanel.jsx` — the original
top-right aside — was deleted once `FrameContent.jsx` took over its job; `PrimarySummary`,
`MethodList` and `HelperList` survived from it and are now used inside the frame.

Drive it with `scripts/flow_agent.py`: `isolate:<node_id>` clicks the control and `isolated` reports
the box, its canvas fill and its computed border. To exercise **frame content** in the harness,
`/flow-fixture` accepts `?repo=<name>` (`App.jsx: fixtureAnalysis`) so `useNodeExplanation` actually
fires; stub the response with Playwright's `page.route("**/explain", ...)`. Without a `repo` the hook
short-circuits and the frame correctly reads `no explanation available for this node`.

## 5.5. The editable-diagram slice — built, not wired

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
- **"The diagram is missing loads of files" is measured and is NOT an indexing bug.** On
  django-helpdesk: 128 `.py` files, 28 excluded as tests by `render_repo.read_python_sources`, 100
  indexed → 484 functions, 139 classes, **0 unparsed**, 2570 call sites, **554 forks extracted**.
  The judge returns **225 decision / 282 guarded_step / 47 noise**, and the graph carries 222
  decision nodes. Only 24 of the 100 files end up with a node, but of the 76 without one: 40 are
  Django migrations, 18 have no function defs at all (settings/config), 4 have functions but zero
  branches, and the remaining 14 *do* branch — and every one of their 31 forks was extracted and
  judged **`guarded_step` (27) or `noise` (4), never `decision`**. Those 14 are template tags,
  `manage.py`, DRF `serializers.py` and similar: framework-invoked code whose only branches are
  guards. Nothing is being dropped by the indexer, the call resolver or the condenser. Before
  chasing "missing files" again, re-run the numbers — the lever is the judge prompt, not the
  pipeline.
- **Expanding `entry:seed:src.helpdesk.email` produces 1 overlapping node pair on django-helpdesk**
  (`entry:seed:...forms.AbstractTicketForm` vs `dec:...create_object_from_email_message:593`).
  The collapsed view is clean — `flow_agent.py <repo> state overlaps` reports `OVERLAPS: 0` — so
  this is `childPlacement`/`expansionBoxes` mis-spacing a revealed child against the skeleton row
  below it, not a skeleton layout bug. Isolate does not cause it and happens to resolve it while
  active, which is why `overlaps` reads 0 mid-isolate and 1 after Escape.
- **A repo map analysed before a pipeline change keeps serving the old shape.** `symbol_context`
  (and its `calls` field, §5) lives in the persisted map, so features that depend on new fields read
  as broken until the repo is re-analysed. Check `updated_at` on the `repo_maps` row before
  concluding a feature is faulty; compare against a fresh `render_repo.py` run of the same repo.
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
