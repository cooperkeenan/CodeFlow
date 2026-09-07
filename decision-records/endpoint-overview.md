# Endpoint Overview and API Contracts

**Status:** accepted
**Recorded against:** commit `6c275719` (2026-09-07) plus the uncommitted endpoint-overview work on
branch `feature/api-contracts`. Re-pin this line to the merge commit when the branch lands.

This record describes why the per-endpoint "API contract" (method, path, params, responses, auth,
examples) is written at **read time** by an LLM rather than during the analyse pipeline, why the
LLM is not trusted with method or path, why a grouped route entry carries one contract per route,
and why no new storage was added to hold any of it.

---

## 1. Why the contract is written at read time, not in the pipeline

`tracer/services/analysis/flow_pipeline.py` produces `flow_graph.json`, and `CLAUDE.md`'s test suite
is that this output is byte-identical for the same repo input. Any step in that pipeline that calls
an LLM at temperature 0 is still, in principle, a live external call whose output can drift — the
decision judge, namer and reviewer already carry this risk and are covered by a content-addressed
cache keyed off `PROMPT_VERSION` for exactly that reason.

Adding contract-writing as a fourteenth pipeline stage would mean every repo analysis pays for up to
one LLM call per endpoint, whether or not anyone ever opens that endpoint's page, and it would widen
the pipeline's non-deterministic surface for a feature most sessions never touch. Endpoint overviews
are viewed selectively — a user opens a handful of endpoints per session, not all of them — so the
natural place to do the work is on the first `GET /repomaps/{repo}/endpoint?entry=<id>` for that
endpoint, in `EndpointDetailService` / `EndpointContractResolver`
(`api/gateway/services/endpoint_detail_service.py`, `endpoint_contract_resolver.py`). The pipeline
stays exactly as deterministic as it already had to be; the contract is an on-demand explain-agent
call, `POST /contract` on `agents/explain_agent`, the same posture as the existing per-node
`POST /repomaps/{repo}/explain`.

## 2. Why the LLM never sees method or path as something to invent

Static analysis owns structure; the LLM owns judgement and words — the same split `node-labelling.md`
describes for node selection. Method and path are not judgement calls: they come from
`shared/flow_endpoints/entry_routes.py::EntryRoutes.of`, which reads `FlowNode.members` when the
entry is a group and otherwise falls back to parsing the node's own label with
`shared/flow_endpoints/route_label.py::RouteLabel` (§4). That pair is the single source of truth
other code reads route shape from (`EndpointDetailBuilder`, `EndpointContractResolver`,
`scripts/endpoint_detail_fixture.py`). Those parsed values are passed
**into** `ContractRequest` as fixed fields (`agents/explain_agent/explain/models/contract_model.py`);
the LLM is asked to describe params, responses, auth and examples around them, not to state them.

`ContractValidator.write` rejects any model output whose `method` or `path` differs from what was
sent in (`agents/explain_agent/explain/helpers/contract_validator.py`), alongside sanity bounds on
param/response counts and text length. A validation failure — or any other exception, including no
API key being configured — falls back to `HeuristicContractWriter`, which derives a contract with no
model call at all: path params from `{brace}` / `<angle>` tokens, and a summary humanized from the
handler name. This is the same offline path `scripts/endpoint_detail_fixture.py` always uses, since
fixture generation has no gateway or API key in front of it.

## 3. Why no new table, and no source embedded into the graph

Two pieces of state a contract needs already have a home:

- **The contract itself** is cached in the existing `explanations` table
  (`shared/explanation_store/neon_explanation_store.py`), keyed by a fingerprint of
  `PROMPT_VERSION` + `entry_id` + `method` + `path` + the sorted `(fqn, source)` pairs fed to the
  model (`EndpointContractResolver._fingerprint`). That table already exists to hold exactly this
  shape of value — an LLM-derived JSON payload addressed by a content hash — for per-node
  explanations, and a contract is the same kind of artifact for an endpoint instead of a node.
  Adding a second table would duplicate its schema for no behavioural difference.
- **Key-method source** is not persisted new at all. `flow_graph.json` never embeds full function
  bodies (only `span`); source is sliced on demand from `code_files`, the same table
  `shared/code_store/neon_code_store.py` already holds the analysed repo's files in, via
  `api/gateway/services/symbol_context_resolver.py::SymbolContextResolver.slice_for`. Embedding
  source directly into the graph was considered and rejected: it would bloat `flow_graph.json` (and
  therefore its cache-invalidation fingerprint) with text nobody asked for on most requests, for
  data `code_files` already stores once per file regardless of how many endpoints reference it.

`scripts/endpoint_detail_fixture.py` is the one exception, and deliberately so: the offline fixture
writer has no `code_files` table to read from, so it slices source directly off the local repo on
disk (`span.file` under the given `repo_path`) into the static fixture JSON it writes — the same
`span`-driven slicing, just against a filesystem instead of Postgres.

## 4. Why a grouped route entry gets one contract per route

`EntryFinder._grouped` (`analysis/routes/entry_finder.py`) folds two or more routes sharing a module
into a single `entry:group:<module>` node, labelled `auth · 3 routes`. That fold is what keeps the
whole-repo map inside its 15-node budget and is not being undone here.

The endpoint page originally inherited the fold wholesale and described only the **first** member. On
mealie's `entry:group:mealie.routes.auth.auth` that meant the page showed `POST /token` alone;
`GET /oauth` and `GET /oauth/callback` were silently absent, and the panel still said "3 routes". The
label also never parsed — `RouteLabel.parse` only accepts a leading all-caps verb, so `auth · 3
routes` yielded `method=""`, `path="auth · 3 routes"`, which the OpenAPI export then emitted as a
nonsense path under a guessed `get`.

`FlowEntry.members` already held every handler FQN but was dropped at condensation. `FlowNode` now
carries `members: list[RouteMember]` (`handler_fqn`, `method`, `path`), populated by
`FlowEntry.route_members` and forwarded through `GraphAccumulator.upsert`. `EndpointDetailService`
resolves one contract per member — each with that member's own handler source promoted in the symbol
payload — and `EndpointDetail.contracts` is a list.

Two consequences worth stating:

- **`members` is additive to `flow_graph.json`.** Verified on the demo repo: the graph is
  byte-identical with the field stripped, and `rendered_view.json` is byte-identical outright. The
  golden check is unaffected in substance, but the file does change, so a stored baseline predating
  this needs recapturing.
- **The whole-repo map still shows one node.** This changes what the *endpoint page* says about a
  group, not how the diagram draws it.

The OpenAPI export benefits directly: `contractsToOpenApi` merges the members into one document's
`paths` object, which is what that object is for — `entry:group:...auth` exports as three operations
under `/oauth`, `/oauth/callback` and `/token` in a single Postman import.

## 5. Where the caches sit

- **Contract payloads** — `explanations` table (Neon), keyed by the fingerprint above. No
  in-process cache in front of it beyond the response-level `EndpointViewCache`.
- **The assembled `EndpointDetail` response** (contracts + key methods + sliced sources) —
  `EndpointViewCache`, an in-process LRU keyed on `(user_id, repo, updated_at, "detail:<entry_id>")`
  (`api/gateway/services/endpoint_view_cache.py`), the same cache the whole-repo and per-endpoint
  flow views already share. `updated_at` in the key means a re-analysed repo invalidates every
  cached detail for free.
- **The `FlowGraph` a detail is built from** — `FlowGraphCache`, the same in-process LRU
  `EndpointDetailService` already depends on for the flow views.
- **Source file content** — `code_files` (Neon), read through `SymbolContextResolver`, with a
  per-request `file_cache` dict avoiding repeat fetches of the same file for multiple key methods.

None of these are watched by `uvicorn --reload` if changed while the gateway is running — see
`CLAUDE.md`'s `shared/` restart trap, which applies here exactly as it does to the rest of
`shared/flow_endpoints/`.
