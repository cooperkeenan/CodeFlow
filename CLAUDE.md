# CodeFlow — Claude Code Guidelines

## Workflow — Opus plans, Sonnet implements, Opus reviews
- Feature work is split into small, self-contained scoped task docs ("PBIs"). A planning model (Opus)
  designs the approach, spawns a Sonnet sub-agent to implement each scoped task, then reviews the
  resulting diff before it is accepted.
- Scoped task docs are **ephemeral** — they are gitignored and removed on merge to main. Do not rely
  on their numbers or continued existence; this file and the code are the source of truth.

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

## Naming
- Classes: PascalCase
- Functions/variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Private methods: prefix with _

## File Structure
- One class per file unless the secondary class is a private implementation detail
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

- `path_fqn.agent_root_of` keyed on the literal `"agents"`, so on a repo laid out as
  `app/<service>/src` nearly every internal call resolved to `ext:` and the call graph was shredded.
- `service_root_resolver.root_of` had the identical bug, collapsing four services into one lane.

Both are now derived from where imports actually resolve. Do not reintroduce the pattern. The same
rule covers domain terms: framework support (FastAPI, Django) is legitimate; searching for "agent",
"tool", or one project's idioms is not.

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

## Determinism
Same repo in → byte-identical `flow_graph.json` out. Sort every set/dict iteration; break ties on
`(file, line, name)`. LLM calls run at temperature 0 behind a content-addressed cache — bump the
prompt's `PROMPT_VERSION` when the prompt changes, or stale cached verdicts are silently reused.

## Static Analysis Owns Structure
Static analysis finds every candidate fork and builds the graph. The LLM judges which forks are
real decisions and writes their human-readable labels. The LLM must never add, remove, merge or
rewire a node or edge.

## Do Not Weaken Checks To Go Green
Never loosen an assertion, invariant or budget to make a run pass. If a check genuinely no longer
applies, say so and leave it failing — a red assertion is information. Report honest negatives with
the real numbers rather than presenting a partial result as success.