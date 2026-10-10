# Endpoint Diagrams & Read-Path Caching

## Endpoint diagrams (`shared/flow_endpoints/`)

The whole-repo map answers "what is this codebase"; it does not answer "what happens when this
endpoint is called". That second view is built **at read time in the gateway**, not in the tracer
pipeline — it slices one entry out of the stored `FlowGraph` on request.

`EndpointCatalog` lists the `entry:` nodes, splitting real HTTP routes from `entry:seed:` /
`entry:trivial:` service entry points. `EndpointSubgraph.slice(graph, entry_id)` (whole-entry view) takes the
containment closure from that entry, keeps only intra-slice edges, prunes back edges into a
deterministic DAG (`BackEdgePruner`), records which targets fell outside, and hands the result to
`EndpointElider` (`DEFAULT_BUDGET = 16`, `_MAX_PASSES = 3`), which runs:

`ChunkDissolver` (undo the whole-repo `more:`/`fold:` placeholders — there is room inside one
endpoint) → `SharedHelperCollapser` (fold owners used by ≥10 endpoints into one `helper:` node) →
`RunCollapser` (fold linear runs of ≥3 steps into one `run:` node) → then a loop of `IslandDemoter`
→ `FanoutCapper` (≤5 children per parent) → `EndpointRanker` (only if still over budget; BFS
distance, then kind, then how *exclusive* the owner is to this endpoint) → `LevelAssigner` →
`TerminalCloser` → finally `SoleChildPromoter`. Every pass has a floor of 10 nodes.

`OwnerSubgraph` slices from any `owner_fqn` rather than an entry, producing a **helper diagram** for
a shared function. It reuses `EndpointSubgraph.slice_root` — same closure, pruning and elision, just
rooted somewhere that is not an entry.

### Group views (`?entry=<group id>`)

Per-route views are gone. `EndpointGroupTree.build(graph)` splits each route entry at read time into a
forest of **endpoint groups** (`GroupSplitter`: literal URL segments, max 8 / min 3 routes per group,
small buckets pooled into balanced "other" chunks; root group id == entry id). A leaf is drawn by
`GroupSubgraph` (`GroupScope` = union of `RouteScope`, sealed hop regions, `HopCollapser` into
`helper:` nodes, second back-edge prune preferring path pairs, path nodes `protected`, elider budget 16);
a non-leaf by `GroupOverview` (one `endlink:<child id>` node per child). `GroupPaths` returns
`meta.paths` per member: `node_ids`, `edges`, `reveal`, `missing_edges`. The gateway's `GroupViewService`
caches `group:<id>` and adds `group` and `paths` to the response. Full detail:
`decision-records/endpoint-groups.md`; tracer-side paths: `decision-records/happy-path.md`.

### Cross-diagram links

`LinkResolver` maps node id → `EndpointLink{kind, target, label}` for one slice. It runs at read
time and is returned **beside** `view` in the HTTP response — deliberately **not** stored on
`FlowNode`, so `flow_graph.json` is untouched and the golden check is unaffected. Four sources:

- `endlink:<entry_id>` — the cut-off call lands on another endpoint → link to that endpoint.
- `endcont:<owner_fqn>` — the cut-off call lands on ordinary code → link to that function's helper diagram.
- `helper:<owner_fqn>` — a `SharedHelperCollapser` fold → link to that helper's diagram.
- a visible terminal whose `owner_fqn` is shared by ≥2 endpoints.

Two restrictions stop the links being noise, and both were added after measurement: only **visible**
(`level == 0`) nodes are considered, since a link on a hidden node can never be clicked; and a link
is suppressed when its target owner is **already drawn in the current view**, because that just
reopens what the reader is looking at. On django-helpdesk this is 22 links across 8 of the 32 endpoint diagrams.

## Read-path caching

Endpoint views are recomputed per request — DB read, two Pydantic validations, a graph slice, and an
HTTP round trip to the render agent — so both layers cache.

Server (`api/gateway/`): `RepoMapStore.updated_at()` is a cheap `SELECT updated_at` that does **not**
read the 2–3 MB `jsonb` payload; it is the version key. `FlowGraphCache` (LRU 8) holds the validated
`FlowGraph` per `(user, repo, updated_at)`; `EndpointViewCache` (LRU 200) holds the rendered response
per `(user, repo, updated_at, view_key)` where `view_key` is `home`, `entry:<id>` or `helper:<fqn>`.
Both are app-state singletons — `deps/` builds services per request, so a per-request cache would be
useless. `shared/caching/lru_cache.py` is the shared primitive.

`ETag` is a hash of the **response body**, not of the cache key. An earlier version keyed it on
`(user, repo, updated_at, view_key)`, which meant a rendering or elision code change left
`updated_at` untouched, the server returned `304 Not Modified`, and the browser rendered a stale
diagram forever. Keep it content-derived.

Client: TanStack Query v5 (`frontend/src/api/queries.js` holds every key and fetcher in one place, so
hooks and prefetches cannot drift). `staleTime` 5min, `gcTime` 30min. Hovering an endpoint row or a
saved-map row prefetches its view, so the click is usually instant.

