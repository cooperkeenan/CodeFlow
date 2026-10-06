# Static Happy Path per Route

**Status:** accepted
**Recorded against:** commit `ace1548d` (2026-10-06) on branch `feature/static-happy-path`. Re-pin
this line to the merge commit when the branch lands.

This record describes what a route's "happy path" is, why it is derived statically rather than by an
LLM, which signals and which ranking rule choose it, how helper calls and delegation are handled,
how it survives the whole-repo budget stage, and how the read side slices a per-route diagram around
it. Paths live in `tracer/services/analysis/paths/`; the read side is in `shared/flow_endpoints/`.

---

## 1. What it is, and why it is static

A happy path is the ordered list of node ids a successful request to one route walks through, from
the entry node to the route's terminal (a `ret:` outcome or a response effect). It is stored per
route on `RouteMember.happy` as `HappyPath{node_ids, hops, ends_in_failure}` in `flow_graph.json`.

It is static for the reason `node-labelling.md` §1 gives: static analysis owns structure, the LLM only
labels. The walker never reads `llm_label`, a verdict or any LLM output. Its inputs are the graph,
the fork arms (`Arm.outcome`, `Arm.terminal`, `Arm.label_source`) and the project index. Because arm
edges now carry `FlowEdge.arm_index`, the walker maps an edge back to its `Arm` through
`ArmSignalIndex` even after the LLM has relabelled the edge. Same repo in, same path out.

**Terminal naming and the fingerprint.** `ret:` terminals are named by the existing flow namer, not
by a new LLM call. `TerminalNodeBuilder.emit` gives them a static label of the form
`<Class.method>: <return expression>` (owner-qualified, full expression, status code kept). That
label is the namer's fingerprint evidence. A bare `return 302` label once gave every redirect the
same fingerprint, so seven different redirects shared one cached LLM label from `kb.vote`. Do not
shorten the label back to the status code.

## 2. Signals the walker uses

- **Arm outcome** (`syntax/arm_outcome.py::classify_outcome`): `failure` if the arm's last statement
  is a `raise` or returns a call with status >= 400 (status via `status_call_label` or a `status=` /
  `status_code=` keyword); `success` for any other return; `continue` if the arm falls through.
  `with` bodies recurse, an `if/else` combines both sides (both failure = failure, any continue =
  continue). Stored on `Arm.outcome`; not part of any fingerprint.
- **Arm terminal** (`returns` / `raises` / `falls_through`) for the early-exit tie-break.
- **Tested verb**: a `method == 'POST'` style test in the arm's `label_source`.
- **Reach**: how many route-owned nodes are reachable from a candidate (`ReachCounter`).
- **Failure oracle** (`FailureOracle`): an edge is failing if its arm outcome is `failure` or its
  target is a `ret:` whose statement classifies as a failing return. An *implicit terminal* is a
  `ret:` node with no `return`/`raise` statement at its line (the synthetic "Completes").

## 3. Ranking rule

`CandidateRanker.choose` takes the outgoing walkable edges (`sequence`, `arm`, `parallel`; sorted by
`(arm_index < 0, arm_index, target, kind)` in `PathGraph`) and:

1. Drops failure edges. If nothing is left it falls back to all edges and flags the walk
   `forced` (this becomes `ends_in_failure`).
2. Filters by the route's verb (`_by_verb`): edges testing that verb, else edges testing no verb,
   else all. `ANY` and empty verbs skip the filter.
3. Sorts by, in order: most route-owned reach (descending); non-`out:` before `out:`; explicit
   terminal before implicit terminal; continuation before an arm that returns or raises early;
   non-arm before arm edges; lower `arm_index`; target id.

`ReachCounter` counts route-owned nodes reachable *through* helper regions (capped at 300 nodes), so
an arm that saves via a helper and then redirects is not scored zero. The early-exit tie-break is why
`ViewTicket.get` renders instead of taking its `close` shortcut.

## 4. Phases, hops, owners and delegation

`HappyPathWalker.walk` has two phases, both with a visited set.

**Wrapper phase.** `Arm.wrappers` are the project decorators around a Django view.
`DjangoViewResolver._unwrap` peels `path('', protect_view(X.as_view()))` down to the inner view
(previously this resolved to the decorator and produced a bogus `ANY` endpoint) and records the
decorators that resolve to project functions. The walker moves entry -> wrapper nodes -> the route's
`head` (`RouteMember.head`, set by `RouteAssembler`). If the head is not reachable, the path stops
there.

**Handler phase.** From the head, repeatedly pick the next edge by §3 while on a route-owned node.
Stop at an `outcome` node or a `response` effect.

**Owners and delegation.** `RouteOwners.of(handler)` is the handler plus its delegation chain.
`DelegationResolver.resolve` follows a handler whose body is a sole `return call(...)` into the
callee, including `View.as_view()(...)` into the class's first project method among
get/post/put/patch/delete/dispatch via `MroMethodFinder`. Nodes owned by any function in the chain
are "route-owned".

**Hops.** A node reached whose owner is not in that set is a *hop* (a call into a helper). It is
recorded in `HappyPath.hops`, and `HopFinder.resume` does a bounded breadth-first walk (300 nodes)
through the helper's region to the earliest route-owned node not yet visited, preferring nodes at or
after the calling line. `PathGraph.is_walkable_target` forbids entry nodes and heads of *other*
routes' own handlers, but a shared helper that merely happens to head another route is crossable
(`a7c91167`).

## 5. Terminals: nested and implicit

`RouteAssembler` places every route: a head node, a splice of project decorators ahead of the
handler, and pure delegation followed into the callee. `RouteTerminalBuilder` ensures a `ret:` node
for the route's last return/raise. `TerminalNodeBuilder.close_arm` gives every arm of a route
handler (or delegate) that ends in a return or raise its own `ret:` node, including a return at the
end of an arm that has other nodes, and a closed arm no longer feeds the decision's continuation.
A handler that falls off the end gets an implicit `Completes` terminal (still owner-qualified).
`StepMerger` never absorbs a head.

## 6. Carrying the path through the budget stage

The whole-repo budget stage merges and folds nodes, which could delete or rename a node the stored
path points at. So path nodes are **pinned** (`BudgetWorkGraph.pins`, gathered from every member's
`happy.node_ids`): `ArmFolder` never drops a pinned arm; `BudgetRecondenser` only merges pairs where
both or neither end is pinned; `EffectCapper` keeps a pinned effect. Every merge records an alias
(`graph.alias(old, new)`), and `HappyPathRemapper.remap` rewrites `node_ids` and `hops` through
`BudgetWorkGraph.resolve` before export, dropping consecutive duplicates and asserting every final id
exists. A failing assert means a new merge path forgot to alias.

## 7. Route view slicing (read side)

`RouteSubgraph.slice(graph, entry_id, handler_fqn)` returns `None` unless the member has a non-empty
happy path.

- `RouteScope` picks the nodes: the path, nodes owned by the handler/head owner reachable from it
  (cap 80), a bounded region (cap 60) behind each hop, and one hop of context.
- `SliceAssembler` builds the working `SliceGraph` (`working`), prunes back edges preferring path
  edges, and assembles the result (`finish`).
- `HopCollapser` replaces each hop's region with a single `helper:<owner>` node (via
  `SharedHelperCollapser.fold`), then **discards the inner nodes** and zeroes `folded_count`, so it
  is a linkable node with no `+N` expansion (an earlier version expanded into ~60 nodes). It then
  adds an edge from the helper to the next path node so the path stays connected.
- `EndpointElider.elide(..., pins=path)` never demotes or caps pinned nodes. If the path alone
  exceeds the budget, `PathCompressor` folds the window of interior path nodes with the fewest
  decisions into one `run:` node. Entry views are byte-identical when no pins are given.
- `HappyPayload.build` raises if a path node is not visible or two neighbours have no direct edge.

## 8. API and payload shape

`GET /repomaps/{repo}/flow?entry=<id>&route=<handler_fqn>` is routed by `FlowPayloadService`
(`helper` first, then `entry`+`route`, then `entry`, else whole map) to `RouteViewService`, which
loads via `FlowGraphLoader`, renders via `FlowViewRenderer`, and caches under
`route:<entry>|<handler_fqn>` in `EndpointViewCache`. The normal endpoint view payload gains:

```
route: {handler_fqn, method, path}
happy: {node_ids: [...], edges: [[source, target], ...], ends_in_failure: bool}
```

Fixtures: `scripts/repo_home_fixture.py` writes `route_<slug(entry)>__<slug(handler)>.json` beside the
endpoint fixtures with the same `route` and `happy` keys.

Frontend: selecting a contract card loads that route's view (single-route endpoints preselect);
`useHappyHighlight` marks nodes and edges listed in `payload.happy` (`rf-happy`), dims the rest and
fits the camera to them; `ends_in_failure` adds `rf-happy-failure` (amber) and a header note.
`happyPath.js` (a frontend regex heuristic) is deleted; the backend is the only source.

## 9. Checking it

`scripts/happy_path_check.py <out_dir>` (needs `flow_graph.json`) slices every route and must exit 0.
Per route it asserts: `member.happy` non-empty, starting at the entry, every id in the graph; payload
non-empty, starts at the entry, no duplicates; every payload node present and visible (level 0);
a direct edge and a listed payload edge between each neighbour pair; `visible_before_promote` <= 16;
the path ends on an outcome or response effect unless `ends_in_failure`; and routes sharing a
`(handler, wrappers)` key have identical payloads. The per-entry overview counts are information only.

## 10. Known limits

- **ANY routes.** A Django view registered for all verbs has no verb to filter on, so GET vs POST is
  resolved only by reach and the §3 tie-breaks; the chosen branch can be the wrong verb's.
- **Delegation with no project method.** An `UpdateTicketView`-style view whose delegate has no
  project-defined get/post/... ends at the handler's own `ret:` node for its delegating `return`
  (e.g. `staff.update_ticket_view: return UpdateTicketView.as_view()(…)`), not inside the view.
- **Budget.** The 16 budget applies before `SoleChildPromoter`, which may push a route view past it.
  Measured on django-helpdesk (`venv/bin/python scripts/happy_path_check.py scratch_out/hp_final`):
  48 routes, 0 failures, visible max 17 (`followup_edit`: 15 before promote), mean 5.1,
  1 route `ends_in_failure` (`raw_details`, ends at `raise Http404`).
- **Long paths at small viewports.** The pane frames the path at `minZoom 0.5`. A path taller or
  wider than the pane at that zoom is partly off screen and must be panned: on django-helpdesk at a
  ~745x742px pane, 4 of 48 routes (`BaseCreateTicketView.dispatch`, `ViewTicket.get`,
  `followup_edit`, `view_ticket`). Lowering the zoom would make labels illegible.
- **Region caps.** Hop regions, reach and scope are capped (300 / 80 / 60 nodes); a very large helper
  region can mean the walker does not resume.
- **Not a trace.** It is the most likely success line, not a runtime proof; data-dependent branches are
  chosen by the rule in §3.
