# Tech Stack & Tooling

## Tech Stack
- **Python 3.10 exactly** (venv at `venv/`), FastAPI, Uvicorn, Pydantic v2. A newer interpreter
  changes `ast.unparse` output and breaks the golden diff — see the skill's "The Python Version Trap".
- Anthropic SDK, `claude-haiku-4-5-20251001`, temperature 0 (decision judge, stitch judge, labeller).
- psycopg + Neon Postgres for persistence (`shared/repo_map_store/neon_repo_map_store.py`).
- React + Vite + React Flow, TanStack Query v5 for the read path. Positions come from the render
  agent — no dagre, no Mermaid.
- Python-only analysis; JS/TS is not traced.

## Tooling

```bash
python scripts/render_repo.py <repo> [out]        # pipeline → JSON + decision list
python scripts/render_repo.py --no-llm <repo>     # force the deterministic heuristic judge
python scripts/screenshot_flow.py <repo>          # → scratch_out/flow.png via headless Chrome
python scripts/screenshot_flow.py --save <handle> <repo>   # also save to a user account
python scripts/profile_scope.py <repo>         # what the LIVE pipeline fetches (profiler scope); exit 1 if any .py is missed
python scripts/selfrun.py                         # in-process self-analysis (2 known failures)
python scripts/flow_agent.py <repo> <action>...   # drive the real page in a browser
python scripts/flow_metrics.py <out_dir>          # structural harness, must exit 0
python scripts/happy_path_check.py <out_dir>      # group-view happy-path harness, must exit 0
python scripts/_verify_imports.py                 # all 5 services import cleanly
python scripts/render_tour.py                     # regenerate the /tour payload
python scripts/dump_explain.py <out_dir> --list   # explain-agent payload for a node
```

### `flow_agent.py` — drive the diagram without a human relaying screenshots

Playwright (`requirements.txt`; uses the installed Chrome via `channel="chrome"`, so
no browser download) opens the real `FlowPage` and runs a sequence of actions. It reports the
rendered page **as text**, so state can be asserted rather than eyeballed.

```bash
python scripts/flow_agent.py <repo> --rebuild state overlaps
python scripts/flow_agent.py <repo> "toggle:<node_id>" fit "shot:scratch_out/x.png"
python scripts/flow_agent.py <repo> "press:collapse all" state
```

Actions: `state` (every visible node with position, label, `+N` control and a `[→]` marker for a
cross-diagram link), `overlaps` (colliding node pairs — **0 is the goal**, and this is the check that
catches bad layout), `toggle:<id>`, `link:<id>` (follow a link chip), `click:<id>`,
`press:<button text>`, `key:<name>`, `fit`, `shot:<path>`, `endpoint:<entry_id>` (open that
endpoint's overview page from the repo home list), `detail` (print the endpoint page as text:
method, path, title, description, contract param/response counts, the `generated` note, and
key-method names), `method:<fqn>` (click that key-method row, assert its code pane is non-empty),
`back` (return from method code to the key-method list), `diagram` (press "view diagram" and wait
for the canvas), `route:<handler_fqn>` (click that route's contract card in the group page; highlights its happy path inside the group diagram, no reload), `happy` (compare the group diagram's `data-happy-ids/-edges` with the rendered `rf-happy` nodes and edges, and print `happy: N expected, M highlighted, K on screen, E/X edges`), `sidebar` (print every row of the `/flow` endpoint sidebar with its active flag).
Flags `--entry <entry_id>` and `--home` open one endpoint's diagram or the repo home page instead of
the whole map. `--rebuild` re-runs the pipeline first; without it the existing fixture is reused.
Nested expansion works — toggle a revealed decision or a `more:` node to go deeper.

`happy_path_check.py` reads `<out_dir>/flow_graph.json`, builds the endpoint-group forest, slices each
route's leaf group (`build_group_subgraph`) and asserts, via `happy_path_rules.py`, a non-empty path from
the entry, every path node visible after its `reveal` list, a direct edge between neighbours, a view within
the 16 budget before promotion, an end on a terminal (or `ends_in_failure`) and identical paths for twin
members; plus every route in exactly one leaf, leaf size <= 8 unless overflow, and an `endlink:` per child
in every overview. One row per route and a summary; exit 1 on any failure.

Fixtures: `group_fixture.py` writes one fixture per endpoint group (and `repo_home_fixture.py` a `groups`
list); the per-route `route_*.json` fixtures no longer exist.

This is also the **only** check that catches a frontend render loop — `vite build` passes happily
while the page is unusable. Run it after any `frontend/src/` change.

`screenshot_flow.py` serves the result to the real `FlowPage` through a dev-only `/flow-fixture`
route — no API, DB or login. `--save` upserts a `repo_maps` row viewable in the web UI, resolving
the account by `github_login` or `email`.

