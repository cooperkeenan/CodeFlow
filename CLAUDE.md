# CodeFlow — Claude Code Guidelines

## Workflow — Opus plans, Sonnet implements, Opus reviews
- Feature work is split into small, self-contained scoped task docs ("PBIs"). A planning model (Opus)
  designs the approach, spawns a Sonnet sub-agent to implement each scoped task, then reviews the
  resulting diff before it is accepted.
- Scoped task docs are **ephemeral** — they are gitignored and removed on merge to main. Do not rely
  on their numbers or continued existence; this file and the code are the source of truth.

## Repository Layout

Four deployable backend services plus an on-demand explain agent, a shared library and a frontend.
**Each service directory is the Docker build context; the code inside it lives in a uniquely-named
package.** That nesting is deliberate — see "Never Use Generic Top-Level Package Names" below.

```
api/                     gateway   — build context, Dockerfile CMD is `uvicorn main:app`
  main.py  run.py                    (stay at top level)
  gateway/                           the package: imports are `from gateway.…`
    core/ clients/ models/ routers/ services/ deps/
agents/profiler_agent/   → package `profiler`
agents/tracer_agent/     → package `tracer`
agents/render_agent/     → package `render`
agents/explain_agent/    → package `explain`
shared/                  real top-level package, imported by everyone as `shared.…`
scripts/                 developer tooling (see Tooling)
frontend/                Vite + React + React Flow
```

## Never Use Generic Top-Level Package Names
Every service used to expose top-level `services/`, `models/`, `core/`, `routers/`. Any script that
put two services on `sys.path` silently got whichever came first — `agents/render_agent/models/
render_model.py` was genuinely unimportable from `render_repo.py`, `selfrun.py`, `screenshot_flow.py`
and `flow_agent.py`, and `dump_explain.py` needed a `services.__path__.append(...)` hack that broke
if any import moved. Every service's code now lives under its own package name. Do not reintroduce a
bare `services/` or `models/` at a service root.

When adding a service, keep `main.py` at the build-context root and put everything else in the
package — the Dockerfile does `COPY ${SERVICE_DIR}/ ./` with `PYTHONPATH=/app`, so `/app/<pkg>/`
resolves and `uvicorn main:app` still works with no Dockerfile change.

## The `.env` Path Trap
Each service's `core/config.py` locates the repo root by index:
```python
try:    ROOT_DIR = Path(__file__).resolve().parents[N]   # local dev → repo root
except IndexError: ROOT_DIR = Path(__file__).resolve().parents[M]   # in-container → /app
```
**If you move a config file up or down a directory, BOTH indices change.** The `except` branch is the
container path and no local test exercises it. `scripts/_verify_imports.py` will not catch a mistake
here because it injects env vars explicitly. This has broken three times; check both branches and
simulate the `/app/<pkg>/core/config.py` case before claiming it works.

## The Python Version Trap
This project is pinned to **Python 3.10** and the venv at `venv/` is built on it. Always run
`venv/bin/python` and `venv/bin/ruff`, never a bare `python3` — on at least one dev machine `python3`
resolves to Homebrew 3.14, and that silently breaks two things:

- `ast.unparse` renders some nodes differently across versions (3.14 emits
  `{i for i, _ in t}` where 3.10 emits `{i for (i, _) in t}`). That text lands in `raw` fields in
  `flow_graph.json`, so **the golden diff fails for a reason that has nothing to do with your change.**
  If you see a one-line diff in a `raw` field, check your interpreter before debugging your code.
- PEP 695 generics (`class JsonCache[T]:`) parse on 3.12+ and are a `SyntaxError` on 3.10. Use
  `TypeVar`/`Generic`. This has already broken the tracer once.

If the venv is missing, rebuild it with `/opt/homebrew/bin/python3.10 -m venv venv` and
`venv/bin/python -m pip install -r requirements-dev.txt ruff`, then re-run the golden diff to confirm
the environment is faithful before trusting any other result.

## Restart Services After Changing `shared/`
The services run under `uvicorn --reload`, and each watches **only its own directory** — `api/` for
the gateway, `agents/<name>/` for an agent. Nothing watches `shared/`. Change
`shared/flow_endpoints/` or `shared/models/` and every running service keeps serving the old code
indefinitely, with no error and no reload line in the log.

This has already produced a full round of false conclusions: a diagram was judged "still too busy"
and cross-diagram links "not working" when both had been fixed hours earlier and the gateway was
simply 18 hours stale. Before believing anything you see in the browser against the live API, check
the worker start time (`ps -o lstart= -p $(lsof -ti:8000)`) against your edit times, and restart if
it is older. The fixture routes driven by `flow_agent.py` do not have this problem — they read
regenerated JSON, not the running gateway.

## Design Principles
- SOLID principles on every file:
  - Single Responsibility: one class, one reason to change
  - Open/Closed: extend via new classes, not by modifying existing ones
  - Liskov Substitution: subtypes must be substitutable for their base types
  - Interface Segregation: small focused interfaces over large ones
  - Dependency Inversion: depend on abstractions, inject concretions

## Code Standards
- Max 150 lines per file — split if exceeded
- Type annotations on all function signatures
- Constructor injection only — no global state, no service locator
- No markdown docstrings or inline comments explaining what code does
- No unsolicited tests
- No unused imports
- Prefer dataclasses for value objects
- Follow existing patterns before introducing new ones

### One class per file — and its one exception
The rule holds for anything with behaviour. It does **not** hold for zero-behaviour declarations,
where a 7-line file per item is the rule producing the worse outcome. These are grouped on purpose:
- `Protocol` declarations → `services/analysis/contracts.py`
- frozen value-object dataclasses → `tracer/models/{index_records,call_records,sites,verdicts,naming}.py`
- thin `dict` read-indexes → `analysis/resolve/indexes.py`
- single-function builders → a per-package `factory.py`
- pure AST/string helpers → `analysis/syntax/`

Do not extend this exception to classes that do work. When you group, say so; do not do it silently.

## Naming
- Classes: PascalCase
- Functions/variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Private methods: prefix with _

## File Structure
- Services take all dependencies in __init__ via constructor injection
- Tools wrap exactly one service method — no logic in tool handlers
- Schemas live next to the tool they describe (same file)

## What Not To Do
- Do not modify frontend/ unless the PBI explicitly says so
- Do not create test files unless asked
- Do not refactor files that are not in scope for the current PBI
- Do not add logging statements beyond what already exists in the file being modified
- Do not use global variables or module-level mutable state

## Never Hardcode This Repo's Own Layout
CodeFlow analyses arbitrary Python repos, so any assumption about directory names is a bug —
and one that is invisible when testing on CodeFlow, because CodeFlow satisfies its own
assumptions by construction. This has already cost two separate outages of the whole feature:

- FQN resolution (now `analysis/syntax/paths.py`) once keyed on the literal `"agents"`, so on a repo
  laid out as `app/<service>/src` nearly every internal call resolved to `ext:` and the call graph
  was shredded.
- `analysis/indexing/service_root_resolver.root_of` had the identical bug, collapsing four services
  into one lane.

Both are now derived from where imports actually resolve. Do not reintroduce the pattern. The same
rule covers domain terms: framework support (FastAPI, Django) is legitimate; searching for "agent",
"tool", or one project's idioms is not.

## The Golden-Graph Check Is The Test Suite
There are no unit tests. Determinism is the regression check: **same repo in → byte-identical
`flow_graph.json` out.** Capture a baseline before any refactor and diff after every step:

```bash
python scripts/render_repo.py "$LOCAL_REPO_PATH" scratch_out/baseline   # once
python scripts/render_repo.py "$LOCAL_REPO_PATH" scratch_out/after
diff scratch_out/baseline/flow_graph.json scratch_out/after/flow_graph.json   # must be empty
```

For a pure refactor a non-empty diff means you changed behaviour — find it, do not rationalise it.
This is especially sharp around `analysis/fingerprints.py`: those hashes key the LLM verdict cache in
`.cache/`, so any change to a hashed input causes a cache miss, a live LLM call, different labels and
a broken diff. Do not clear `.cache/` mid-refactor and do not bump a `PROMPT_VERSION` unless you mean
to invalidate every cached verdict.

Note that a **CodeFlow self-run legitimately changes** whenever CodeFlow's own files move. Use the
non-CodeFlow demo target as the golden file; treat `selfrun.py` as a smoke test only.

## Always Run It And Look At The Picture
Every change to the pipeline, the graph or the layout ends with the same loop, every iteration —
not once at the end:

```bash
python scripts/screenshot_flow.py --save cooperkeenan <repo>
```

Then **open `scratch_out/flow.png` with the Read tool and actually look at it**, and ask whether
what you see is the goal — not whether the code ran. Counts are not evidence. Overlapping nodes,
spaghetti edges, empty canvases and 50-node fans all pass every assertion in this repo. Metrics
here have improved several times while the diagram got visibly worse.

`--save cooperkeenan` writes the run to the user's account in the same pass, so they never have to
re-run it themselves. Always include it.

To check *interaction* rather than the static image, drive the real page yourself instead of asking
the user to relay what they see:

```bash
python scripts/flow_agent.py <repo> --rebuild state overlaps
python scripts/flow_agent.py <repo> "toggle:<node_id>" fit "shot:scratch_out/x.png"
```

`state` prints every visible node with its position and `+N` control; `overlaps` lists colliding
node pairs and **must be 0**. Assert on that output — it catches layout regressions that a
screenshot alone hides.

**A frontend build passing means nothing.** An infinite React render loop compiles cleanly; only
`flow_agent.py` catches it. Any change under `frontend/src/` ends with a real browser drive.

Also run the structural harness, every iteration, alongside the two above — not instead of them:

```bash
python scripts/flow_metrics.py <out_dir>
```

It must **exit 0**. It prints containment shape (roots, depth, body sizes, the fork/chain split)
and asserts the parts that really are invariant: a single-rooted DAG, total reachability, cohesion,
and zero overlapping node boxes in the rendered view. The rest of what it prints — the I3
single-entry count, body_kind counts, fork vs. chain counts — is context for a human, not a
pass/fail gate. See the next rule for why.

## The Flow/List Ratio Is Not A Quality Metric
A decision's arms are mutually exclusive alternatives, so a fork is correctly `body_kind == "list"`
— that is not a regression. A falling flow/list ratio, on its own, tells you nothing about whether
the diagram got better or worse. Judge forks and chains **separately** (`scripts/flow_metrics.py`
prints both), and settle any real disagreement by opening the PNG, not by staring at the ratio.

## Validate On A Repo That Is Not CodeFlow
Never accept "it works" from a CodeFlow self-run alone. Use the demo target
(`LOCAL_REPO_PATH`, currently `django-helpdesk`). CodeFlow satisfies its own assumptions by
construction, so a self-run hides exactly the bugs that matter.

## The Top-Level Diagram Is At Most 15 Nodes
The first thing shown is the whole codebase at a high level: **max 15 nodes.** Detail is not
deleted to achieve this — it is demoted to a deeper visibility level and reached by expanding a
branch. Expanding a branch shows the decisions sitting *between two nodes*, so a single expansion
must stay small too; a `+` that reveals 50 nodes at once is a bug, not disclosure.

## Endpoint Diagrams Get Their Own Budget
The whole-repo map and a single endpoint's diagram are budgeted separately.
`shared/flow_endpoints/endpoint_elider.py` slices one entry at read time with `DEFAULT_BUDGET = 16`,
which is the "at most 15 nodes" rule above applied per endpoint. The budget is not a hard ceiling:
`SoleChildPromoter` (below) can push a view a little past it, so the observed range on the demo repo
is 2–19 visible nodes, mean 8. The whole-repo budget stage is separate: it works to
`skeleton_budget = 15` / `node_budget = 40` and is a different tuning surface. Changing one does not
affect the other.

Two interactions are load-bearing and easy to undo by accident:

`SoleChildPromoter` runs last and pulls any node that is its host's **only** hidden child back into
view. This exists because `useExpansion.js` implicitly expands a lone hidden child anyway — demoting
one achieves nothing except rendering it inside an expansion box with ~250px of dead space. Removing
the promoter re-introduces boxes and makes medium diagrams worse, not smaller.

`TerminalCloser` must never assert a continuation that does not exist. It emits a terminal only when
the node genuinely has an external successor (naming it, and linking to it via `endcont:<owner_fqn>`),
or an entry-node target (`endlink:<entry_id>`). When there is no successor anywhere in the graph it
emits **nothing** and the node is left as a leaf. An earlier version emitted a node labelled
"Continues" in all cases: on django-helpdesk that was 31 terminals, a tenth of every visible node, of
which only 4 had any continuation — for the other 27 the label was simply false.

## Decision Records
`decision-records/` is tracked (unlike ephemeral scoped task docs) and holds long-lived descriptions
of how a subsystem works and why. Each record pins the commit it was written against. **When you
change logic a record describes, update the record in the same commit and re-pin it** — a stale
record is worse than none, because it will be believed.

## Determinism
Same repo in → byte-identical `flow_graph.json` out. Sort every set/dict iteration; break ties on
`(file, line, name)`. LLM calls run at temperature 0 behind a content-addressed cache — bump the
prompt's `PROMPT_VERSION` when the prompt changes, or stale cached verdicts are silently reused.

## Static Analysis Owns Structure
Static analysis finds every candidate fork and builds the graph. The LLM judges which forks are
real decisions and writes their human-readable labels. The LLM must never add, remove, merge or
rewire a node or edge.

## A Thing Present In The DOM Is Not A Thing The User Can See
`flow_agent.py state` proves an element exists; it does not prove anyone can see it. The
cross-diagram link chip shipped as a bare arrow glyph at 9px inside a 15px box — correct in the DOM,
asserted green, and about **7 screen pixels** once `fitView` zoomed the canvas to 0.47. The user
reported the feature as missing and they were right.

When you add an affordance, work out its size *at the zoom the page actually renders at* and open the
PNG. Scale new chrome against something already known to be legible in a screenshot (the
`file:line` provenance line is the useful yardstick), not against the unzoomed CSS pixel.

## Do Not Weaken Checks To Go Green
Never loosen an assertion, invariant or budget to make a run pass. If a check genuinely no longer
applies, say so and leave it failing — a red assertion is information. Report honest negatives with
the real numbers rather than presenting a partial result as success.

`scripts/selfrun.py` currently has two failing assertions, both pre-existing and both left red on
purpose: its expected lane set is stale (it does not account for `explain`, and `scripts` is being
detected as a service root, which may itself be a lane-detection bug), and one guard-selector
decision survives the judge. Fix the underlying cause or leave them failing; do not edit the
expected values to match observed output.

Lint is also honest rather than green: `ruff check .` reports pre-existing errors (mostly `B008`,
FastAPI's `Depends()` in a default argument, which has no `ruff.toml` suppressing it). The rule is
**no new errors**, not zero. Import-order (`I001`) churn caused by moving files is fine to fix with
`ruff check <path> --select I001 --fix`, but never run an import sorter over `scripts/dump_explain.py`
— its imports are order-dependent around a mid-file `sys.path.insert`.
