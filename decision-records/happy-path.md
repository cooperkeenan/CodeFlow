# Static Happy Path per Route

**Status:** accepted
**Recorded against:** commit `8ec577ee` (2026-10-07) on branch `feature/static-happy-path`. Re-pin
this line to the merge commit when the branch lands.

This record describes what a route's "happy path" is, why it is derived statically rather than by an
LLM, which signals and which ranking rule choose it, how helper calls and delegation are handled,
and how it survives the whole-repo budget stage. Paths live in `tracer/services/analysis/paths/`.
How paths are drawn (per endpoint group, not per route) is in `endpoint-groups.md`.

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

## 7. Reading it back

The stored `RouteMember.happy` is consumed at read time by the endpoint-group views (leaf diagram,
`paths` payload with `node_ids` / `edges` / `reveal` / `missing_edges`, highlight, fixtures, the
check). See `endpoint-groups.md`. The per-route view (`RouteSubgraph`, pins, `PathCompressor`,
`HappyPayload`, `?route=`) was removed.

## 8. Known limits

- **ANY routes.** A Django view registered for all verbs has no verb to filter on, so GET vs POST is
  resolved only by reach and the §3 tie-breaks; the chosen branch can be the wrong verb's.
- **Delegation with no project method.** An `UpdateTicketView`-style view whose delegate has no
  project-defined get/post/... ends at the handler's own `ret:` node for its delegating `return`
  (e.g. `staff.update_ticket_view: return UpdateTicketView.as_view()(…)`), not inside the view.
- **Budget.** Group-view budget and viewport limits are in `endpoint-groups.md` §8.
- **Region caps.** Hop regions, reach and scope are capped (300 / 80 / 60 nodes); a very large helper
  region can mean the walker does not resume.
- **Not a trace.** It is the most likely success line, not a runtime proof; data-dependent branches are
  chosen by the rule in §3.
