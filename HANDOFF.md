# Handoff — Progressive-disclosure decision diagram

Read this first. It states the next job, what already works, and every known gap.

Branch: `featue/decision-nodes`. Open PR: #14.

**Start at §13 — that is the next job.** Progressive disclosure, pillar nodes, the tree layout,
fractal containment and depth scaling are all built and verified on `django-helpdesk` (§6, §8–§12).
The working tree is dirty and uncommitted by design, for review.

§13 in one line: **one `+` should reveal one decision (the most important), and lines from outside
should stop at the dotted box instead of threading through it.**

---

## 1. The job

The diagram currently renders everything it has chosen to show, all at once, in one flat page.
The user wants **progressive disclosure**:

- **One high-level diagram of the whole codebase**, always visible. This is the skeleton — the
  services, entry points and major outcomes. It must stay readable at a glance.
- **A `+` / `−` control per branch** that reveals or hides the decisions sitting *between* a parent
  and its outcomes. Expanding one branch must not disturb the rest of the page.
- The high-level view is never navigated away from. There is no drill-down to a separate page —
  detail is spliced into the diagram in place.

The user's reference sketch:

```
                 Orchestrator
                /            \
        (Correct Product ID?)  (Correct Product ID?)
              |                       |
        Regulatory Agent           MRF Agent
              |                       |
     (Do we need both services?)   (CPM Data?)
        /        \                    |
     CPT Tool   MUE Tool          Query MRF Data
```

Grey = outcomes (services, agents, tools, handlers). Orange = decisions. **The orange nodes are
what `+` reveals.** Note their position: a decision sits *on the edge* between a parent and its
outcome. Collapsed, `Orchestrator → Regulatory Agent`; expanded, `Orchestrator → (Correct Product
ID?) → Regulatory Agent`.

That shape matters for the data model. A decision is best treated as an **edge annotation that
gets promoted to a node on expand**, not as a node that is hidden and shown. Modelling it as a
hidden node forces the layout to reflow the whole page on every toggle.

### Design constraint that is currently violated

The backend today **destroys** decisions to fit a page budget (`BudgetConfig.node_budget = 40`,
`visible_decisions = 8`). For progressive disclosure the backend must instead **emit the full tree
with a visibility level per node**, and let the frontend decide what to draw. Folding must become
reversible metadata, not deletion. This is the single biggest change required.

---

## 2. What already works — do not rebuild it

| Stage | Where | State |
|---|---|---|
| Import resolution | `services/analysis/path_fqn.py` | ancestor-prefix, layout-agnostic |
| Service roots | `service_root_resolver.py` + `project_indexer.py` | derived from imports |
| Fork extraction | `dispatch_extractor.py` + `*_detector.py` | branch/match/except/route/table/polymorphic/dynamic |
| **Decision judging** | `llm_decision_judge.py`, `prompts/decision_judge_prompt.py` | LLM decides real decision vs guard, writes the question |
| Verdict cache | `verdict_cache.py`, `decision_fingerprint.py` | content-addressed, prompt-versioned |
| Entry points | `fastapi_route_scanner.py`, `django_route_scanner.py` | FastAPI + Django URLconf |
| Tree geometry | `placement/tree_layout.py`, `tree_structure.py` | tidy tree, parent centring, cycle-safe |
| Screenshot loop | `scripts/screenshot_flow.py` | renders any local repo to a PNG |
| Account save | `scripts/repo_map_saver.py` | `--save <handle>` writes a viewable `repo_maps` row |

**The demo/test repo is `django-helpdesk`**, cloned at `/Users/cooperkeenan/github/django-helpdesk`
and set as `LOCAL_REPO_PATH`. It is a support-ticket system: relatable for a demo, conventional
Django routing, and decision-dense. Its decisions read like *"User can access ticket?"*, *"Create
new ticket or update only?"*, *"User has queue access?"*, *"User is superuser?"*.

---

## 3. Gap analysis

### 3a. Blocking the main job

**G1 — RESOLVED, and the original diagnosis was wrong.** The claim "most decisions never reach the
graph" is false. Measured at the pipeline seam: `FlowCondenser` + `FlowStitcher` emit **253 nodes
containing 222 of the 225 judged decisions**. The decisions always arrived; `PageBudgeter` deleted
214 of them to fit `node_budget=40` (`DecisionDissolver._contract` removed each decision *and every
node reachable only through it*). Folding is now reversible metadata — see §6. `DecisionSeeder`'s
flat `entry:seed:<root>` anchor is real but is a hierarchy wart, not a cap on arrivals.

**G2 — MEASURED; one open product decision.** The drawn skeleton on django-helpdesk is **31 nodes,
8 roots, max depth 2**. Those 8 roots are not fragmentation — every one is a genuine entry point
(`kb · 4 routes`, `public · 2 routes`, `staff · 36 routes`, `ANY login/`, `ANY`, and 3
`entry:seed:*` anchors). Getting to literally 1 root requires **inventing a synthetic repo-root
node that does not exist in the code**. That is a product call and was deliberately left to the
user. Separately, the skeleton had 128 edges over 31 nodes (a circuit board); the render agent now
picks a spanning tree (23 edges) and marks the other 105 `secondary`, faded to 25% and toggleable
via "show cross-links".

**G3 — RESOLVED.** `+N` / `−` controls exist on every expandable node (`ExpandToggle.jsx`,
`useExpansion.js`), with "collapse all" and a `?expand=<ids>` dev param for screenshotting.

**G4 — RESOLVED, decided as follows.** A decision is *both* an edge annotation and a child:
`FlowEdge.hidden_path` carries the ordered decisions spliced onto a skeleton edge, and
`FlowNode.hidden_children` carries the immediate decision successors of any node. Edge annotation
alone was tried first and **failed**: only 59 of 222 decisions sit on a path between two skeleton
nodes, so 163 terminal decisions would have been unreachable in the UI. `hidden_children` reveals
one level at a time and nests, which is what makes disclosure progressive.

### 3b. Detection limits (known and documented — not bugs to "fix" blindly)

**G5 — SDK-mediated HTTP is invisible.** `effect_registry.py` detects outbound HTTP by matching
httpx/requests/aiohttp method names. A call made *inside* a third-party SDK (e.g.
`agent_framework.a2a`) produces no `EffectSite`, so no cross-service candidate exists.
`LlmStitchDetector` is built, cached and working — it correctly returns "no match" on genuine
third-party calls — but on TA_Platform it has nothing to judge. Widening effect detection to
recognise a client constructed with a URL argument would create the candidate.

**G6 — Decisions expressed as classes are invisible.** DDD-style codebases encode rules as objects:
`class SellerMustBeEligible(BusinessRule): def is_broken(self) -> bool: return ...`. There is no
fork, so fork detection sees nothing. This is a real limitation of the technique and worth stating
plainly in the dissertation rather than papering over.

**G7 — Plugin/dynamic routing is invisible.** django-oscar wires views through
`OscarConfig.get_urls()` and a string-keyed `get_class()` service locator. Supporting it would mean
hardcoding one project's idioms — correctly rejected.

### 3c. Engineering debt

**G8 — Lint and types.** `ruff check .` fails with ~200 errors; **193 of these pre-date this work**
(mostly `B008` function-call-in-default-argument and unsorted imports on `main`). Roughly 8 were
added recently. `mypy` reports 6 errors, 2 of them ours in `llm_decision_judge.py:69,91` (indexing
`dict[str, Any]` with `Any | None`). CI runs both and has been red on `main` for a while.

**G9 — CD is not gated on CI.** `.github/workflows/cd.yml` triggers on push to `main`, builds five
backend images and runs `railway redeploy`. Its `deploy` job only `needs: push-images`, so a red
lint never blocks a deploy. **The frontend is not in the pipeline at all** — it is served via the
Cloudflare tunnel (`tunnel.sh`).

**G10 — Branch deploy.** `featue/decision-nodes` is pushed and current. Deploying the branch
directly via `scripts/build-push.sh` rather than through the `main` pipeline was asked about, never
done, and is still open.

**G11 — Ranking is only half-effective.** `DecisionAdmitter._score` now orders by
`(importance, score)`, but with only 8 of 225 decisions present the ordering rarely bites. Re-check
once G1 is fixed.

**G12 — Host disk.** The dev machine ran out of space mid-session. `ENOSPC` kills `Bash` entirely,
since it cannot write its own output file. Keep temp files small and clean up after yourself.

---

## 4. How to run and verify

```bash
cd /Users/cooperkeenan/GitHub/CodeFlow && source venv/bin/activate

python scripts/render_repo.py /Users/cooperkeenan/github/django-helpdesk /tmp/hd   # JSON + decision list
python scripts/render_repo.py /Users/cooperkeenan/github/django-helpdesk /tmp/hd2  # run twice
diff /tmp/hd/flow_graph.json /tmp/hd2/flow_graph.json                              # must be empty

python scripts/selfrun.py                                                          # 5 assertions, must pass
python scripts/screenshot_flow.py /Users/cooperkeenan/github/django-helpdesk       # PNG of the real page
python scripts/screenshot_flow.py --save cooperkeenan <repo>                       # also save to the account
```

`scratch_out/flow.png` can be opened with the Read tool. **Look at it every iteration** — in this
project the metrics improved several times while the picture got worse. `--no-llm` forces the
deterministic heuristic judge. The verdict cache is at `.cache/decision_verdicts.json`; deleting it
costs a cold re-judge (~4 min on django-helpdesk, ~12 min on django-oscar).

For frontend work, `/flow-fixture` renders the real `FlowPage` against
`frontend/public/fixture/rendered_view.json` with no API, DB or login.

---

## 5. Constraints

- `CLAUDE.md` is law: ≤150 lines per file, one class per file, constructor injection, type
  annotations, no docstrings or explanatory comments, no unsolicited tests.
- **Determinism**: same repo in → byte-identical `flow_graph.json` out. Sort every set/dict
  iteration; break ties on `(file, line, name)`. The LLM runs at temperature 0 behind a
  content-addressed cache; bump `PROMPT_VERSION` when a prompt changes, or stale verdicts get reused.
- **Static analysis owns structure.** The LLM judges significance and writes labels. It may never
  add, remove, merge or rewire a node or edge.
- **No domain hardcoding.** Framework support (FastAPI, Django) is fine. Searching for "agent",
  "tool", or one project's idioms is not.
- **Validate on a repo that is not CodeFlow.** Two separate bugs here were invisible because
  CodeFlow satisfies its own assumptions by construction — see `CLAUDE.md`.
- Never weaken an assertion to make a run pass. If one genuinely no longer applies, say so and leave
  it failing.

---

## 6. Progressive disclosure — what landed

### Model (`shared/models/flow_graph.py`)

- `FlowNode.level` — `0` = skeleton (always drawn), `1` = revealed on expand. Every `decision` is
  level 1; entries/steps/effects are level 0 unless demoted to fit the page.
- `FlowNode.hidden_children` — immediate level-1 successors. This is what a `+` reveals, and it
  nests: a revealed decision carries its own `hidden_children`.
- `FlowEdge.hidden_path` — the ordered decisions spliced onto a skeleton edge when expanded. A fork
  to two outcomes puts the same decision in *both* edges' paths; the frontend dedupes by id, which
  reconstructs the fork exactly as the reference sketch draws it.

### Tracer — `VisibilityBudgeter` replaces `PageBudgeter`

`recondense → arm-fold → effect-cap → mark levels → apportion → SkeletonReducer → SkeletonProjector`.
Nothing is deleted. When a lane's skeleton exceeds its budget, `SkeletonReducer` **demotes** the
lowest-ranked step/effect to level 1 rather than removing it. `page_budgeter.py`,
`page_budgeter_factory.py`, `decision_admitter.py`, `decision_dissolver.py` and `lane_reducer.py`
are deleted.

`budget_invariants.py` was rewritten, not weakened. The old node-ceiling and ≥1-arm assertions no
longer describe the model; the new ones assert that every `hidden_path` id exists and is level 1,
that skeleton-edge endpoints are level 0, that **every level-1 node is revealed by some parent**,
and that every node is reachable from an entry.

### Render — skeleton only, with reserved expansion space

`FlowPagePlacer` lays out level-0 nodes and skeleton edges only. `HiddenEmitter` emits level-1
payloads (unpositioned) plus, per expandable node, **collision-free relative offsets**: it scans
rightward a column at a time until the children's boxes clear every already-occupied box, then
claims that space. Expanding therefore never overlaps or reflows the rest of the page. Geometry
stays backend-owned; the frontend only adds vectors. `RenderedView` gained `hidden` and
`hidden_edges`.

### Frontend

`useExpansion.js` holds the expanded set, walks `hiddenChildren` recursively, positions each child
at `parent.position + (dx, dy)`, dedupes shared decisions, and keeps only edges whose endpoints are
both visible. `ExpandToggle.jsx` is the orange `+N` / `−` control in `NodeChrome`. `FlowPage` adds
"collapse all", "show cross-links", and a `?expand=<ids>` param.

### Measured on django-helpdesk (was → now)

| | before | after |
|---|---|---|
| decisions in `flow_graph.json` | 8 of 225 | **222**, all revealable |
| nodes drawn collapsed | 43 | 31 (+3 lane headers) |
| skeleton edges drawn | 128 | 23 tree + 105 faded |
| determinism (graph and view) | — | byte-identical across runs |

`scripts/selfrun.py` is 4/5. The one red assertion — *no guard-selector decision survives* — is
left failing on purpose. It regex-matches `\bnot\b` in a label and catches
`'Token valid and not revoked?'`, which reads like a real decision. It used to pass only because
the destructive budget happened to delete that node; it now surfaces a pre-existing judge/regex
question. Do not tune the regex to go green — decide whether the check is the right check.

### Open

- Whether to invent a synthetic repo root to force 1 root (G2).
- `DecisionSeeder`'s flat `entry:seed:<root>` anchor still owns 52 immediate children on
  django-helpdesk — the largest single `+`. Giving it real hierarchy is the next readability win.

---

## 7. Navigation and visual cleanup

Seven defects found and fixed. The geometry cluster shared one root cause: **three unreconciled
node-size models** (`flow_grid_config` 200×72, `hidden_emitter` 200×112, and the real frontend CSS).

**`shared/models/node_geometry.py` is now the single source of truth.** `NODE_GEOMETRY` is keyed by
the `shape` strings `shape_for()` already emits; `geometry_for()` raises on an unknown shape rather
than defaulting, because silent defaults are how the drift happened. It is emitted on
`RenderedView.node_geometry`, so the frontend renders with the exact numbers the layout used and
cannot go stale.

| Defect | Fix |
|---|---|
| Decision text painted outside the diamond at the **median** label length | Decisions are now a rounded rect with an orange left border (`◇` glyph retained). `ClippedShape.jsx` deleted — its content layer had no `overflow:hidden`, which was the mechanical cause. `LABEL_STYLE` gained a 2-line clamp + ellipsis, and `NodeChrome` a `title` tooltip, for every node kind. |
| Camera never re-fit after expanding | `CameraController.jsx`, rendered **inside** `<ReactFlow>` so `useReactFlow()` works without a provider. Translates the **minimum** amount to bring the reveal on-screen, preserving zoom, and skips entirely when it is already visible. |
| Legend covered the fit-view button | Controls moved to `top-left`. Corners are now distinct: Controls TL, Legend BL, MiniMap BR, Provenance TR. |
| Every expand click also opened the provenance popover | `ExpandToggle` now stops the `click` event too — `pointerdown` does the work, but `click` is a separate event with its own propagation path. Verified: toggle leaves 0 nodes selected; a deliberate node click still selects. |
| 0px gap between stacked decisions | `row_step` is derived from the geometry registry (`max(height) + row_gutter`), so a gap is structural, not a coincidence of two constants matching. |
| Collision reserve pushed nodes to `dx=1920` | Real per-shape AABB test instead of one invented 200×112 box; reservation order is `(y, x, id)` so a visually-earlier node is not robbed of its column by an alphabetically-earlier one. |
| Effect nodes had no expand control | `EffectNode` routes through `NodeChrome`, which now takes an optional subtitle. One component owns the expand affordance. |

Also: 208px of dead spacer rows removed from `_layout_forest` (`subtree_gap_rows` 1 → 0), cutting
diagram height 1400 → 1108, and large reveals lay out as a compact block (max 4 rows/column)
rather than one tall stack.

**Multi-branch expansion.** The backend cannot know which combination of branches is open, so it
reserves against skeleton nodes only. `useExpansion` resolves the rest at expand time, shifting a
colliding block down until clear. Without this, expanding 5 branches gave 12 overlaps; with it, 0.

Verified on `django-helpdesk`: overlaps 0 collapsed and across 5 expanded branches including nested
`more:` chains; both `flow_graph.json` and `rendered_view.json` byte-identical across runs;
`selfrun` unchanged at 4/5.

---

## 8. Top-down tree layout

User feedback: "two lines from kb are too close, one line is purple, it's too rectangular — make it
flow like a tree." Investigation found three real defects, not just styling.

**Two different trees.** `tree_layout.build_forest` decided node *positions* (parent = deepest
predecessor) while `SkeletonSpanner` decided which edges were drawn *bold* (BFS from root). They
agreed on only **3 of 7** edges — so `kb → Create Ticket Cc` was drawn bold across the page while
`Create Ticket Cc`'s actual positional parent (`Merge Ticket Values`) was faded, and `staff → its
3 children` was faded despite being real structure. `LaneBand` now carries `tree_pairs` from the
forest it actually used, so bold edges match placement **by construction**. `skeleton_spanner.py`
is deleted. Every primary edge is now exactly one row (dy=100).

**The purple line** was the "spine" — intentional but degenerate: the router found exactly **1
spine edge out of 33**, highlighting one arbitrary link. Removed, along with its legend row.
Position now carries the hierarchy.

**Rectangular routing.** Nodes exposed top/bottom handles, but `useGraphTransform` forced
`sourcePosition:'right'` / `targetPosition:'left'` while `tree_layout` places children *below*.
Every parent→child edge therefore exited right and re-entered left — a forced orthogonal detour.
Now `bottom`→`top` with `getBezierPath` at low curvature (research: readability correlates with
low curve complexity; radial layouts measurably lose to traditional/orthogonal — Burch et al.,
IEEE TVCG 2011).

**Expansion inserts a layer.** Previously reveals fanned sideways. Now children are emitted
*below* the parent (centred, max 3 per row) and `useExpansion` pushes every node below the parent
down by the block height — so `A → C` becomes `A → B.a → C` with the gap opening to make room, and
lane bands below shift too. Where a skeleton edge's `hidden_path` is fully revealed, that edge is
hidden because the real chain now draws it. Revealed edges are also classified tree vs cross-link,
so only parent→child links draw solid.

Verified: overlaps 0 collapsed and expanded; both JSON outputs byte-identical across runs;
`selfrun` unchanged at 4/5.

---

## 9. Pillar nodes

Three subagents investigated: the handle bug, what importance signals already exist, and published
techniques for finding architecturally significant components.

**Edges left the sides of nodes.** Root cause: `Handles.jsx` rendered four *unnamed* handles
(Left/Top target, Right/Bottom source). React Flow's `getHandle()` returns `bounds[0]` whenever an
edge carries no `sourceHandle`/`targetHandle` — so it always picked Left and Right. The
`sourcePosition:'bottom'`/`targetPosition:'top'` set in `useGraphTransform.js` were **dead code**:
React Flow only forwards them as props into the custom node, which ignored them. `Handles` now
renders exactly one target and one source, positioned from those props, so the existing plumbing
finally means something.

**`Src · other decisions`** came from `DecisionSeeder._anchor_for`, which bucketed orphan decisions
by coarse *service root*. It now keys on `ComponentIndex.component_of` and, before fabricating
anything, looks for an existing node backed by the same component and attaches there. Labels are
real component names (`Email`, `Queue`, `View Ticket`); the phrase is gone.

**Pillars.** Research (Zaidman & Demeyer 2008; PageRank/HITS key-class detection; arXiv:2506.07683 on
utility-hub false positives) pointed at HITS over the component call graph. HITS was chosen over
PageRank because it yields two scores — *hub* (calls many important things → coordinators) and
*authority* (depended upon → domain entities) — and the reference sketch's examples are all
coordinators.

Empirically on django-helpdesk (77 components), **hub** gives `views.staff` 0.625, `urls` 0.129,
`email`, `ViewTicket`, `update_ticket` — a real mental model. **Authority degenerates**: seven
`forms.*` classes tie at exactly 0.04390. And `UtilityDamper`'s p90 fan-in filter classes
`models.Ticket` and `user.HelpdeskUser` as "utilities" — the two most important domain objects in a
helpdesk. So: **hub score only, and the utility filter is deliberately NOT applied to it** —
utilities have near-zero hub by construction, so no exclusion is needed and that trap is avoided.

New: `models/pillar_scores.py`, `hits_iteration.py` (fixed 50 iterations, every accumulation over
`sorted()` keys because float addition is not associative, rounded to 6dp), `pillar_ranker.py`,
`pillar_gateway_selector.py` (one node per component), `seed_anchor_folder.py` (keeps the top 3
seed anchors per lane by hub score, folds the rest behind the top one). `SkeletonReducer` now ranks
on `(is_gateway, hub_score, kind, out_degree, backing, id)`.

Verified: both JSON outputs byte-identical across runs; `selfrun` unchanged at 4/5; overlaps 0;
mypy unchanged.

### Honest state

The top level is now component-shaped (`Email`, `Create Ticket View`, `Open Tickets By Queue`,
`staff · 36 routes`) instead of `Query To Base64`. But **only 5 edges are drawn across 15 nodes** —
seed anchors are roots by definition, so `public`, `Open Tickets By Queue`, `Create Ticket View`,
`ANY` and `ANY login/` sit on one row entirely unconnected. The page reads as fragments, not one
flow. Connecting pillars to each other is the next problem, and it is a *structural* one: the call
graph genuinely has no edges between them.

---

## 10. Endpoint drill-down (agreed, PARTIALLY built)

User observation: expanding a `+` shows "random decisions", and API endpoints should each get their
own page. Investigation proved **both observations are the same root cause**.

Expanding `staff · 36 routes` reveals decisions from **seven different functions** —
`delete_checklist_template:2232`, `delete_saved_query:1838`, `email_ignore_add:1876`,
`check_redirect_on_user_query:1087` … i.e. three unrelated endpoints. Across the graph, **46 of 52**
expandable parents reveal decisions from more than one function; only 6 come from a single function.
There is no sequence to show because the parent bundles 36 independent request flows.

### Done

- **Decision provenance restored.** `FunctionProjector._handle_decision` upserted decision nodes with
  no `refs`, so **all 222 decisions had zero `file:line`** despite `PROMPT.md` promising provenance on
  every node. Now passes `refs=[site.span]` (`DispatchSite.span` already existed). Repo-wide
  provenance went 153/292 → **274/292**. Note: passing `backing=[site.owner]` as well was tried and
  **reverted** — it perturbed `DecisionSeeder`'s ancestor logic and stranded 42 nodes.
- **Reveals are ordered by source position.** `SkeletonProjector._hidden_region` sorted children
  alphabetically by id; it now sorts on `(file, line, id)`, so an expansion reads in the order the
  code is written (`user.py:29 → user.py:56 → staff.py:442 → 662 → 778 → 1087 → 1458`).

### Deliberately NOT done — and why

Forcing revealed decisions into a visual chain was **rejected**: the graph already contains **223
decision→decision edges**, so genuine sequences already nest correctly. The remaining fan-out is
decisions from *different endpoints*, which are truly parallel. Chaining them would fabricate edges
that do not exist and violate "static analysis owns structure".

### Next: two-level navigation (agreed with the user, not started)

Agreed shape: **map → endpoint flow.** Top page stays the codebase map (pillars + route groups).
Clicking a route group expands to its endpoints; clicking an endpoint opens that endpoint's own flow
page, where decisions splice in place and *are* genuinely sequential. This **reverses §1's "the
high-level view is never navigated away from"** — the user confirmed the reversal knowingly.

Known caveat to design around: endpoints share large subpaths (every staff view passes through
`ticket_perm_check`, `HelpdeskUser.get_queues`), so per-endpoint pages will repeat common machinery.

Needs: a per-endpoint `FlowGraph` (the tracer already has `FlowEntry.members` and route scanners), a
view-map keyed by endpoint, and frontend routing. `EntryFinder`/`fastapi_route_scanner.py`/
`django_route_scanner.py` already produce the route→handler mapping this would build on.

---

## 11. Fractal containment (dotted box)

User sketch: decisions sit *on the line* between pillars; clicking one opens a dotted box holding a
nested sub-flow that re-joins the next big node. Their question — "shouldn't the smaller decisions
always lead to the next larger node?" — is the right instinct, and measuring it is the key finding.

**Measured on django-helpdesk (222 decisions):**

| | count |
|---|---|
| sit on a line between two pillars (sketch works natively) | **29** |
| do NOT lead to a next larger node | **193** |
| — of those, badged `guarded` (genuine early exit) | 64 |
| — of those, no outgoing edge at all | 69 |
| max nesting depth below a pillar | **12** |

So the alternation holds for only 13% today. The 193 are mostly **legitimate early exits** (a
permission guard returning 403 genuinely ends the request) — the defect is that we draw them as
decisions that simply stop. **Terminal outcome nodes** would make the rule true by construction:
every decision leads either to the next pillar or to a named ending. `arm.terminal` and the
`guarded` badge already carry the signal. *This was recommended first and the user chose the box
first; it remains the prerequisite for the boxes to look complete.*

**Built:** `nodes/GroupBox.jsx` renders a dashed, accent-tinted container. `useExpansion` collects a
box per expansion and `buildBox` sizes it to the bounding box of the owner plus its revealed
children. Nesting is capped at `MAX_BOX_DEPTH = 2` — measured depth reaches 12, and nested boxes
shrink geometrically, so deeper levels expand without a box and should later open as their own page.

**The box and the endpoint page are the same primitive** at different scales: "open this as its own
flow, one way in, one way out". Inline when shallow, a page when deep — so §10's drill-down and this
share a mechanism rather than competing.

Boxes are excluded from the `overlaps` check (`flow_session.py`) and from the header node count —
a container overlaps its own contents by design.

---

## 12. Depth scaling and camera zoom (BUILT)

User: *"every time you go down a level, shrink the size of the boxes and zoom the camera in. You
aren't meant to read it all at once."*

Nodes at depth *d* render at `0.76^d`, floored at `0.42`
(`frontend/src/components/flow/depthScale.js`). Geometry, padding, label/chip/subtitle fonts,
badges, the `+` toggle, edge stroke width and edge labels all scale together, so the shrink is real
DOM size — `flow_session.py`'s `overlaps` check stays honest because `offsetWidth` genuinely shrinks.

`CameraController` then sets `zoom = baseZoom / childScale`, where `baseZoom` is captured at the
first depth-1 reveal and reset by `collapse all`. Apparent size is therefore constant across levels:
deeper is smaller *relative to the page*, but always readable *on screen*.

**Fitting the camera to the revealed block was tried and is wrong** — it makes depth 2 render larger
than depth 1 and discards surrounding context. The reciprocal-zoom rule is the one that works.

Two bugs fixed while landing this, both worth not reintroducing:

- **Child offsets must scale by the PARENT's factor, not the child's.** Scaling `dx`/`dy` by the
  child's factor put the first row inside the larger parent (3 overlaps at depth 2). `dy * parentScale`
  clears the parent's actual height at every depth. Back to 0.
- **A box must bound its whole subtree, not just its direct children.** Otherwise the depth-2 box
  spills outside the depth-1 box — containment that does not contain. `expansionBoxes.js` unions
  each nested box's rect (including its padding) into its parent and paints outermost-first.

Box construction moved to `frontend/src/hooks/expansionBoxes.js` because `useExpansion.js` passed the
150-line limit. Verified on `django-helpdesk`: `OVERLAPS: 0` at depths 1, 2 and 3; collapsed baseline
unchanged at 18 nodes.

---

## 13. Next job — agreed with the user, NOT started

Two changes, both aimed at the same symptom: **one click currently dumps 8 small decisions and a
tangle of lines.**

### 13a. One `+` reveals ONE decision, chosen by importance

> *"instead of having one node with multiple decisions coming out of it, there should just be one
> more decision when you click to zoom in. Otherwise it gets messy with eight smaller decisions.
> This means that you need to prioritize the most important decisions."*

Today `SkeletonProjector._hidden_region` returns **every** immediate non-skeleton successor
(8 for `staff · 36 routes`), and `RevealChunker` splits the overflow into a `+N more` step-node
chain. Wanted: one click → one decision, which itself carries the `+` for the next one.

**The ranking already exists and is currently discarded.** `SignificanceFilter.run` builds
`SignificanceResult.ranked_decisions`, sorted by `(-importance, -score, owner, line, site_id)` —
and **nothing outside `significance_filter.py` ever reads it** (verified by grep). `importance` is a
0.0–1.0 rating the LLM already produces per decision; `decision_judge_prompt.py` explicitly tells it
to rank routing/permission/data-source choices high and error handling and retries low. That is
exactly the signal this job needs. The join is direct: decision node ids are `dec:<site.id>`
(`function_projector.py:115`) and `ranked_decisions` holds site ids.

Suggested shape: `_hidden_region` returns only the top-ranked child; the remainder become hidden
children **of that child**, forming a reveal chain. Nothing is deleted, so every decision stays
reachable, and `RevealChunker`'s `+N more` nodes largely disappear.

**Two constraints that must hold:**

- **A reveal chain is a disclosure order, not a claimed control-flow edge.** §10 rejected forcing
  revealed decisions into a visual chain because 46 of 52 expandable parents bundle decisions from
  *different endpoints*, which are genuinely parallel. Chaining the *disclosure* is fine; emitting a
  `sequence` edge to represent it is not, and would violate "static analysis owns structure".
- **Ordering conflict with §10.** Reveals are currently sorted by `(file, line, id)` so an expansion
  reads in code order. Importance selection overrides that for *which* node appears; keep source
  position only as the deterministic tie-break, which `ranked_decisions` already provides.

### 13b. External edges terminate on the dotted box, not on every node inside it

> *"if you click on a node to drill down, then a lot of the lines overlap. Instead of connecting to
> all other nodes, the lines from the previous nodes should just connect to the outside of that box."*

This is the crossing spaghetti visible in the depth-2 and depth-3 screenshots. Today `useExpansion`
keeps any edge whose endpoints are both visible, so once a box opens, outside nodes still draw one
line each to every node inside it.

Wanted: an edge with exactly one endpoint inside a box retargets that endpoint to `box:<ownerId>`
and the duplicates collapse — N external edges into a box become one line to its border. Edges with
both endpoints inside the same box are unaffected.

Needs: edge rewriting in `useExpansion` (it already knows box membership — `boxes[].members` now
holds the full subtree), plus real `<Handle>`s on `nodes/GroupBox.jsx`, which today renders
`pointerEvents: 'none'` with no handles, so React Flow has nothing to anchor to. Note `box:` nodes
are deliberately excluded from `overlaps()` and the header node count; that stays correct when they
become edge endpoints.

### Still the prerequisite for both

**Terminal outcome nodes** (§11). Only 29 of 222 decisions reconverge to a next pillar; 193 do not,
mostly legitimate early exits drawn as decisions that simply stop. Until an arm ending in a 403 or a
`return None` gets a named ending, boxes will keep looking unfinished and reveal chains will keep
dead-ending. `arm.terminal` and the `guarded` badge already carry the signal.
