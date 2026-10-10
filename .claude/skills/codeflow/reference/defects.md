# Known Limits, Open Defects, Ops & Where Things Live

## Known Limits (by design, worth stating rather than hiding)

- **Decisions expressed as classes are invisible.** DDD `BusinessRule.is_broken()` objects contain no
  fork, so fork detection sees nothing.
- **SDK-mediated HTTP is invisible.** Effect detection matches httpx/requests method names; a call
  made inside a third-party SDK produces no `EffectSite`.
- **Plugin/dynamic routing is invisible.** Supporting one project's service-locator idiom would mean
  hardcoding it. This includes a custom wrapper around FastAPI's verbs (e.g. a gateway's `@route(...)`).
- **Nested git repos / submodules are not analysed.** The profiler excludes any directory with its
  own `.git`; GitHub's tree API omits submodule contents anyway.
- **App-derived lanes are FastAPI-only.** `AppRootDeriver` keys on `FastAPI()` construction; several
  Django projects in one repo get lanes only from import resolution.

## Open defects (honest, with real numbers)

- **The whole-repo map is ~18 nodes with essentially one edge between them.** The skeleton is
  component-shaped, but seed anchors are roots by definition, so most top-level nodes sit on one row
  unconnected. This is *structural* — the call graph genuinely has few edges between top-level
  components — not a layout bug. Endpoint diagrams are now the intended way in and do not have this
  problem; the whole-repo map is the weaker view.
- **Diagrams still sprawl horizontally.** Column assignment allocates width by subtree size, so a
  wide branch pushes its siblings far apart and leaves a large empty middle. Fewer nodes per view
  masked it; the underlying placement is unchanged and is the next real layout problem.
- **`PillarGatewaySelector` scores `entry:group:*` route groups 0** because its scoring reads
  `node.backing`, and route-group entries carry none (they are aggregates). They lose skeleton slots
  to less central `entry:seed:*` anchors that do have backing.
- **Chunked bodies can be `body_kind == "flow"` with `body_head == None`**, which silently disables
  chain re-routing for that body. Not yet root-caused.
- **Single-path decisions render as a command shape but are still labelled as a question.**
  `flow_node_treatment.shape_for` draws a decision with exactly one live arm as `"pipeline"`/`"rect"`
  via `is_linear`, but the label still comes from `DecisionLabeler`, which always phrases a question.
  Fixing it needs a `decision_judge_prompt.py` change and a `PROMPT_VERSION` bump.
- **Sequence bodies rarely chain** — `SequenceChainer` only links same-owner, single-arm-edge,
  same-`owner_fqn` members, so most sequence-shaped bodies render as an unordered set. Chaining one
  that fails those conditions would fabricate an edge that is not real.
- **`scripts/selfrun.py` has 2 failing assertions**, both pre-existing and deliberately left red:
  its expected lane set is stale (does not include `explain`, and `scripts` is being detected as a
  service root — possibly a lane-detection bug worth investigating), and one guard-selector decision
  survives the judge.

## Ops

`.github/workflows/cd.yml` builds the backend images and runs `railway redeploy` on push to `main`;
it is **not** gated on CI, and the frontend is not in the pipeline (served via `tunnel.sh`).
`scripts/build-push.sh` builds and pushes the same images manually.
`action.yml` + `examples/codeflow.yml` are the published GitHub Action, which posts an archive to
`POST /ci/analyse`.

## Where Things Live

- Tracer analysis: `agents/tracer_agent/tracer/services/analysis/` — `flow_pipeline.py` composes it
- Judging: `analysis/significance/` + `prompts/decision_judge_prompt.py` + `analysis/fingerprints.py`
- Entry detection: `analysis/routes/`
- Condensation/budget: `analysis/condense/`, `analysis/budget/`, `analysis/ranking/`
- Geometry: `agents/render_agent/render/placement/{flow_page_placer,tree_layout,tree_structure,flow_emit,vertical_stretcher}.py`
- Endpoint slicing, links, helper diagrams: `shared/flow_endpoints/`
- Read-path caching: `shared/caching/lru_cache.py`, `api/gateway/services/{flow_graph_cache,endpoint_view_cache,etag}.py`
- Run logging and progress: `shared/run_log/`, `api/gateway/services/{progress_plan,progress_tracker,failure_message}.py`,
  `agents/tracer_agent/tracer/services/analysis/{stage_reporter,stage_names}.py`,
  `frontend/src/components/dashboard/Run{Progress,ProgressBar,Phases,LogTerminal}.jsx`
- Subsystem write-ups: `decision-records/` (tracked, commit-pinned)
- Frontend flow page: `frontend/src/pages/FlowPage.jsx`, `hooks/{useGraphTransform,useFlowEditing,useArrowKeyPan}.js`,
  `components/flow/{FlowCanvas,FlowHeader,Breadcrumb,LinkChip,NodeChrome,ProvenancePopover}.jsx`
- Frontend repo home: `frontend/src/pages/RepoHomePage.jsx`, `components/repo/EndpointList.jsx`,
  `api/queries.js` (all react-query keys and fetchers)
- Persistence: `shared/repo_map_store/neon_repo_map_store.py`, `api/gateway/routers/repo_maps.py`
