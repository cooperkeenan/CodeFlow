# Endpoint Groups

**Status:** accepted
**Recorded against:** commit `8ec577ee` (2026-10-07) on branch `feature/static-happy-path`. Re-pin
this line to the merge commit when the branch lands.

This record describes why an endpoint is drawn as a tree of **groups** (one diagram per group) rather
than one diagram per route or per whole entry, how groups are split, where they are computed, how a
leaf group's diagram and its parent overview are built, how the gateway, fixtures and frontend serve
them, and how they are checked. The per-route view that groups replaced is gone; the tracer-side happy
path is in `happy-path.md`.

---

## 1. Why groups

An entry node such as `entry:group:src.helpdesk.views.staff` can fold 48 routes. Drawing all of them
is unreadable (the 16-node endpoint budget cannot hold 48 happy paths); drawing one route per page
loses what the routes share and forces 48 fixtures. A group is a set of at most 8 routes that share
URL structure, so the diagram is sized by code (its routes' union of happy paths) and by URL
structure (what a human would call "the tickets endpoints"). One diagram per group, a tree of groups
per entry.

## 2. The split algorithm (`group_splitter.py`)

`GroupSplitter.split(id, name, entry_id, routes, depth)`:

- Routes are ordered by `(path, method, handler_fqn)`. At most `max_routes = 8` -> one leaf.
- Otherwise bucket by the literal path segment at `depth` (`route_segments.literal_segments`; brace and
  angle params are not literal). Routes with no segment at that depth go in the index bucket `""`.
- One bucket and it is a real segment -> recurse one level deeper. One bucket and it is the index
  bucket -> an `overflow` leaf (more than 8 routes that cannot be separated).
- Buckets with `>= min_routes = 3` routes (and not the index) become sub-groups, split recursively
  with id `<parent>/<segment>` and name `<segment>`.
- All remaining small buckets and the index bucket are **pooled** into balanced "other" chunks: the
  total is divided into `ceil(total / 8)` chunks and keys are packed in sorted order so no chunk
  exceeds 8. A single chunk is named `<name> — other`; several are `<name> — <first>…<last>`, ids
  `<parent>/~<first>`. A chunk over 8 is flagged `overflow`.
- A group id equals its entry id at the root, so the existing `entry:` ids stay valid group ids.
- `EndpointGroupTree._name` takes the root name from `llm_label or label` with the
  `" · N routes"` suffix stripped; `GroupMeta.title` re-adds the live count.

## 3. Read-time placement, and why

Groups are computed in `shared/flow_endpoints` at read time (`EndpointGroupTree.build(graph)`),
not in the tracer pipeline. The pipeline output (`flow_graph.json`, `rendered_view.json`) is
therefore unchanged: the golden diff holds, no LLM verdict is invalidated, and a regroup
(changing 8/3) needs no re-analysis. Root group ids are the entry ids, so whole-repo links, `endlink:`
targets and bookmarks to `?entry=<id>` keep working. The same `shared/` restart trap applies.

## 4. Leaf view (`GroupSubgraph`)

1. `GroupScope` unions one `RouteScope` per walked member: the path, route-owned nodes, one hop of
   context and a region behind each hop. Other routes' path nodes are excluded from a route's regions.
2. `SliceAssembler.working` builds the `SliceGraph`, with **sealed hop regions** (nodes owned only by
   hop regions may not leak into other regions).
3. `HopCollapser` folds each hop region into a `helper:<owner>` node (inner nodes discarded, no `+N`),
   keeping the path connected through it.
4. A **second back-edge prune** runs with all members' consecutive path pairs as preferred pairs, so
   path edges survive and the result is a DAG.
5. `SliceGraph.set_protected` marks every path node. Protected nodes are never absorbed by
   `ChunkDissolver` / `SharedHelperCollapser`; aliases and `resolve_path` map a path through any merge.
6. `EndpointElider` (budget 16) runs as for any endpoint view, then the root gets the group title.
7. `GroupPaths.build` produces `meta["paths"]`, one entry per member: `node_ids` (resolved path),
   `edges` (direct neighbour pairs), `reveal` (ancestors, by level then id, to expand so each path node
   is visible) and `missing_edges` (path neighbours with no direct edge, a check failure).

## 5. Parent overview (`GroupOverview`)

A non-leaf group is a small view: the root plus one `endlink:<child group id>` node per child, titled
with the child's name and route count, one-liner a preview of up to three paths. `LinkResolver` turns
those into links to the child diagram. `meta.paths` is empty.

## 6. Gateway, fixtures, frontend

- Gateway: `GET /repomaps/{repo}/flow?entry=<group id>` -> `FlowPayloadService` tries
  `GroupViewService` (leaf or overview, cached under `group:<id>`; response adds `group` and `paths`),
  then the plain entry view. The repo home payload gains `groups` (the forest summaries). Endpoint
  detail is group-scoped: contracts are those of the group's routes.
- Fixtures: `scripts/group_fixture.py` writes one fixture per group beside the endpoint fixtures
  (`repo_home_fixture.py` includes `groups`); per-route `route_*.json` fixtures no longer exist.
- Frontend: a group tree rail (`GroupTree`), parent pages with child cards (`GroupChildCards`), and
  the leaf diagram pane. Selecting a contract card highlights that route: its `reveal` ids are
  force-expanded, then its `node_ids` / `edges` get `rf-happy`, the rest dims. The layout is never
  changed by selection: the camera frames the path (or its longest legible prefix, from the entry) and
  the user pans for the rest. A client-side "spine" re-layout was built and removed at the user's
  request — they preferred a stable diagram they can move around.

## 7. Checking it

`scripts/happy_path_check.py <out_dir>` builds the forest and, per route, slices its leaf with
`build_group_subgraph` and applies `happy_path_rules.route_failures`: non-empty path from the entry,
all ids in the graph, every path node visible after revealing `reveal`, a direct edge per pair
(`missing_edges` empty), a view within the 16 budget before promotion, a terminal end unless
`ends_in_failure`, and `twin_failures` (members with the same handler and wrappers share a path). Global
checks: every route is in exactly one leaf, leaves have `<= MAX_LEAF_ROUTES` (8) routes unless
`overflow`, every non-leaf overview contains an `endlink:` for each child, views are DAGs. Exit 0.
Refactors of this code are verified by dumping every entry, leaf and overview view over several demo
graphs before and after and requiring byte-identical JSON.

## 8. Known limits

- A long path usually exceeds the pane: paths zigzag across the group layout (up to ~3,800px). The pane
  frames the longest prefix from the entry at the legible 0.5 floor and shows "path continues — showing
  N of M steps"; it never shrinks below legible zoom. `flow_agent happy` reports the rest as off-screen.
- "Other" chunk names are only the first and last pooled segment; they say little about the content.
- Sub-group names are the static literal segment; there is no LLM-written group label.
- A bucket of more than 8 routes with no separable segment is an `overflow` leaf over the cap.
