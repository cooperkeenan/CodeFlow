# 01 — Repository Evolution

Evidence pack for the CodeFlow honours dissertation. Every claim below is traceable to a commit SHA,
file path or command output. Where something cannot be measured from the repository it is marked
`NOT MEASURABLE FROM REPO` with the command that would close the gap.

**Scope of evidence.** The repository spans 7 April 2026 to 7 August 2026. The `main` branch carries
**85 commits**; `--all` reports 131 because several `origin/feature/*` branches hold duplicate
lineages of the same work. All SHAs cited in this document are on `main` unless stated otherwise.
Thirteen pull requests (#1–#8, #11–#15) are merged into `main`; **#9 and #10 do not appear in
`main`'s merge history** and could not be recovered from the local clone.

**Method.** `git log`/`show`/`diff` over all branches; `git log -S<symbol>` to date the introduction
and removal of every named component; `git show <sha>:<path>` to retrieve superseded artefacts.

---

## 1.1 Chronology

Architectural changes only. Routine bug-fix and formatting commits are omitted.

| Date | Commit / PR | What changed | Why (from the commit, PBI or design doc) | Evidence |
|---|---|---|---|---|
| 2026-04-07 | `6af8649` | Initial multi-agent skeleton: `platform_orchestrator`, profiler, tracer, render agents as separate FastAPI apps | Establish the agent-per-service architecture | `git show --stat 6af8649` |
| 2026-04-07 | `78be90f` | **`platform_orchestrator` deleted** (9 files) the same day it was created; orchestration moved into the `api/` gateway | Orchestrator duplicated what the gateway already did | `git log --diff-filter=D -- '*platform_orchestrator*'` |
| 2026-04-13 | `45b0fc1` | `pyan3` + `networkx` added to `requirements.txt` for call-graph construction | First attempt at real edge detection, replacing name matching | `git show 45b0fc1:requirements.txt` |
| 2026-04-14 | `f488aac` | Frontend refactor; `frontend/src/MermaidDiagram.jsx` removed | First retreat from Mermaid as the render target | `git log --diff-filter=D -- '*Mermaid*'` |
| 2026-04-14 | `f0dbeb7` | Render agent created (`render engine`) | Separate placement from tracing | `git show --stat f0dbeb7` |
| 2026-04-14 | `21d52bc` | "Fractal system" — multi-level drill-down (system → module → component) | Objective 3: navigation at multiple levels of abstraction | `git show --stat 21d52bc` |
| 2026-04-21 | `7598d01` | **`pyan3` → `jarviscg`** in `requirements.txt` (`jarviscg @ git+https://github.com/nuanced-dev/jarviscg`) | Flow-sensitive, application-centred call-graph construction (Yan et al., 2023) | `git show 7598d01:requirements.txt`; `git log -S'pyan'` |
| 2026-05-25 | `1e248b5` | `CLAUDE.md`, `PROMPT.md` and the first PBI batch added | Formalises the Opus-plans / Sonnet-implements / Opus-reviews workflow (LO1) | `CLAUDE.md` §Workflow |
| 2026-05-25 | `35df8ff` | **PBI-1–6: evidence-driven tracer accuracy pipeline** — `EvidenceService`, `GraphValidator`, `CorrectionPromptBuilder`, correction loop | Constrain and validate LLM output against static evidence | `git show --stat 35df8ff` |
| 2026-05-27 | `5c3cea9` | **Five `shared/templates/*.json` deleted** (`library`, `microservices`, `monolith`, `spa`, `three-tier`) | The templates forced every repository into one flat three-band layout | `pbis/README.md` §"Not the old `shared/templates/*.json`" |
| 2026-06-02 | `c374738` / PR #4 | Layout agent created (8006) | Split archetype selection from placement | `git show --stat c374738` |
| 2026-06-20 | `3314763` | **Mermaid path deleted**: `mermaid_service.py`, `mermaid_ids.py`, `MermaidDiagram.jsx` | Render agent emitted Mermaid that nothing consumed — `MermaidDiagram.jsx` was never imported | `pbis/README.md` §"Why this work exists" |
| 2026-06-21 | `f7347e1` / PR #5 | Diagram template library: templates as Python placement functions, deterministic React Flow coordinates, no dagre | Same repo in → same diagram out; removes force-directed nondeterminism | `pbis/README.md` §"Locked decisions" |
| 2026-06-28 | `196f9e3` / PR #6 | Service viewer | — | `git show --stat 196f9e3` |
| 2026-07-07 | `08a5690` / PR #7 | Code view: component line ranges, Neon code store, code-serving endpoint | PBIs 34–37 | `pbis/pbi-34..37` |
| 2026-07-07 | `4bffa67` | User accounts, per-user RepoMap storage, CI/CD integration | Persistence and multi-user hosting | `git show --stat 4bffa67` |
| 2026-07-14 | `65b0f1a` / PR #12 | Progress-bar resume (PBI-48) | | `pbis/pbi-48-progress-bar-resume.md` |
| **2026-07-15** | **`f986fa0`** | **Evaluation harness deleted** (`evaluation/`, 8 files, −248 lines); `docs/decision_flow_tracer.md` added (+229) | "Stale, covered only module/edge recall" | `git show --stat f986fa0` |
| 2026-07-15 | `dd9b953` / PR #13 | `features/01`–`13` specification; design revised to v2 | Second review pass found gaps in the v1 design | `docs/decision_flow_tracer.md` v2 note |
| 2026-07-15–16 | `c3a01aa` → `774102a` | **F01–F13 implemented**: FlowGraph models, project indexer, call resolver, dispatch extraction, effect detection, significance filter, condensation, stitching, budget, labelling, layout, frontend, cutover | The decision-algorithm pivot — see `02_decision_algorithm.md` | 13 consecutive commits |
| **2026-07-16** | **`774102a`** | **Cut-over: legacy pipeline deleted.** 111 files changed, +405 / **−5,473**. Removes `ChunkTracer`, `TreeTraversalPartitioner`, `BreadcrumbBuilder`, `ChunkContextBuilder`, `CorrectionPromptBuilder`, `RawMerger`, `GraphValidator`, `EdgeRecovery`, `SpecAssembler`, `EvidenceService`, `CallGraphService`, `AstService`, `HttpVisitor`, and the six placement templates. `jarviscg` removed from `requirements.txt` | "Static analysis owns structure completely; the LLM only names things" | `git show --stat 774102a` |
| 2026-07-17 | `29feecb` | Route entries grouped by router | One-page mental-model surface | commit message |
| 2026-07-18 | `3b4c90d` | `scripts/render_repo.py` — render any local repo to JSON with no API, DB or login | Made the pipeline testable outside the gateway | `PROMPT.md` §Tooling |
| **2026-07-29** | **`991bb11`** | **LLM decision judge replaces the reach heuristic.** `LlmDecisionJudge` batches ~20 forks per temperature-0 call, returning `decision`/`guard`/`noise`, a human-readable question and an importance score | The deterministic reach heuristic could not distinguish an architecturally significant fork from a formatting branch | `git show --stat 991bb11`; `llm_decision_judge.py` |
| 2026-07-29 | `fec2828` | Imports resolved by ancestor prefix, not CodeFlow's own layout | `path_fqn.agent_root_of` keyed on the literal `"agents"`, shredding the call graph on any other layout | `CLAUDE.md` §"Never Hardcode This Repo's Own Layout" |
| 2026-07-29 | `8f84fe2` | `scripts/screenshot_flow.py` — headless-Chrome render to PNG | Made "look at the picture" part of the loop | `CLAUDE.md` §"Always Run It And Look At The Picture" |
| 2026-08-02 | `114399a` | Tree layout; service roots derived from imports | `service_root_resolver.root_of` had the same hardcoded-layout bug, collapsing four services into one lane | `CLAUDE.md` |
| 2026-08-02 | `95f7033` | Budget trimming ranked by importance (HITS hub/authority), not call-graph reach | Reach over-weighted utility code | `pillar_ranker.py`; `95f7033` |
| 2026-08-02 | `d76d67f` | Django URLconf entry-point detection added alongside FastAPI | The demo target is a Django project; FastAPI-only detection found no entries | `django_route_scanner.py` |
| 2026-08-02 | `fd49f05` | `HANDOFF.md` rewritten; docs describing the deleted pipeline corrected | Documentation had drifted from the shipped system | commit message |
| 2026-08-04 | `dd79a6a` | Visibility budgeting: `skeleton_budget=15`, `max_reveal_per_node=8`, `max_body=6`, `seed_anchors_per_lane=3` | Progressive disclosure replaces the destructive one-page budget | `budget_config.py` |
| 2026-08-05 | `bc31dab` / PR #15 | Decision-nodes branch merged to `main` | | |
| 2026-08-07 | `b9779cf` | Isolate/"frame" interaction; `SequenceView.jsx` added | Frame replaces a side panel for symbol detail | `PROMPT.md` §Vocabulary |
| *uncommitted* | working tree | `SequenceView.jsx` **deleted**, replaced by `FlowchartView.jsx` + 7 helper modules (all untracked) | In progress at time of writing | `git status frontend/src/components/flow/isolate/` |

---

## 1.2 The major design pivots

### (a) Hand-rolled function-name matching → `pyan3`

**Before.** The 7 April tracer resolved edges by matching raw callee names across files. The
mechanism survives in the design document's post-mortem: `ast_service._extract_calls` "walks the
whole tree and emits bare callee names. Which function a call lives in, which branch arm it sits
under, whether it's in a loop or an `except` — all discarded"
(`docs/decision_flow_tracer.md` §1.2).

**Problem observed.** Bare-name matching cannot resolve object types or import aliases, so a call
`self._store.save()` yields the token `save` with no way to say which class's `save`.

**After.** `pyan3` and `networkx` added at `45b0fc1` (13 April).

**Evidence it was an improvement.** `NOT MEASURABLE FROM REPO`. No before/after edge counts were
recorded, and the pre-`pyan3` tracer output is not preserved in any commit. The brief's claim that
name matching "produced zero cross-file edges" is plausible and consistent with the design
document's critique, but **there is no artefact in this repository that measures it**. To evidence
it, the 13 April tracer would have to be checked out and run against a fixture repository, counting
edges with and without the resolver.

### (b) `pyan3` → `jarviscg`

**Before.** `pyan3` performs whole-program, flow-insensitive call-graph construction.

**Problem observed.** The motivation is academic rather than defect-driven: Yan et al. (2023)
present JARVIS as flow-sensitive and application-centred, analysing the application rather than the
whole program including its dependencies. The interim report's literature review discusses JARVIS
at nine points (`Interim_Report.docx`, §3.4 Static Code Analysis).

**After.** `7598d01` (21 April) swaps the dependency to
`jarviscg @ git+https://github.com/nuanced-dev/jarviscg`.

**Implementing files.** `agents/tracer_agent/services/evidence/call_graph_service.py` — invoked
`jarviscg` as a subprocess, converted its PyCG-format JSON output, and threaded an
`entry_point_hint` from `shared/models/tracer_request.py`. The `entry_point_hint` field is the one
part of this pivot **still present** in the current codebase
(`shared/models/tracer_request.py`); `call_graph_service.py` itself was deleted at `774102a`.

**Evidence it was an improvement.** `NOT MEASURABLE FROM REPO`. No comparative measurement exists.
The 21 April commit message is "implemented jarvis" with no accompanying metrics.

**Correction to the brief.** This pivot was itself reversed. See (g).

### (c) Free-text tracer output → structured `DiagramSpec`

**Before.** The tracer returned free-text LLM output that downstream stages parsed.

**After.** A Pydantic schema, `shared/models/diagram_spec.py`, constrains the LLM to a fixed shape.
This is a hallucination-mitigation measure: fields the schema does not declare cannot be returned,
and malformed output fails validation rather than propagating.

**Schema evolution.** The current file still carries `ComponentIO` and `ExternalActor`. The recovered
April output (`git show b40216f:shared/outputs/tracer_output.json`, 12,905 bytes) shows the shape in
use at the time — an `architecture_type` of `"three-tier"`, components grouped into
`layers.presentation` / `layers.business`, each with `name`, `description`, `file_path`,
`io.inputs`/`io.outputs` and `children`:

```json
{
  "name": "SessionExecutor",
  "description": "Executes scraping sessions in background tasks with job tracking.",
  "file_path": "src/api/session_executor.py",
  "io": { "inputs": ["job_id: str", "brands: list[str]"], "outputs": ["JobStatusResponse"] },
  "children": ["ScrapingOrchestrator", "BrowserService", "FacebookService", "SessionService"]
}
```

**Status.** `DiagramSpec` is **no longer on the live path.** `shared/models/diagram_spec.py` still
exists but the current pipeline produces `FlowGraph` (`shared/models/flow_graph.py`). Field-by-field
documentation of both is in `06_appendices.md`.

### (d) Evidence grounding and the critic–actor validation loop

**Introduced.** `35df8ff` (25 May), "Implement PBI-1 through PBI-6: evidence-driven tracer accuracy
pipeline". Components: `EvidenceService` (assembled the static facts given to the LLM),
`GraphValidator` (136 lines; checked the returned graph against those facts),
`CorrectionPromptBuilder` (66 lines; turned failures into a re-prompt), `EdgeRecovery`, `RawMerger`.

**Rules and the auto-fix / re-prompt split.** Recovered from
`git show 774102a^:agents/tracer_agent/services/assembly/graph_validator.py`. The brief says "R1–R7";
the actual set is **R1–R6** — there is no R7. Warnings W1–W5 are correct. The split is three-way, and
the 3-iteration cap is confirmed (`for attempt in range(1, 4)` in `tracer_service._correction_loop`,
with the prompt text "This is correction attempt {attempt} of 3"). Full rule-by-rule documentation,
including why the split falls where it does, is in `02_decision_algorithm.md` §2.1.

**Status.** Deleted in full at `774102a`. The design document's justification is explicit: the
correction loop existed to "patch the result back toward the facts", which is only necessary
because the LLM was deriving structure in the first place (`docs/decision_flow_tracer.md` §1.3, §4).
Once static analysis owned structure, the loop had nothing to correct.

### (e) Mermaid → React Flow JSON

**Before.** The render agent emitted Mermaid source; the frontend rendered it via a
`MermaidDiagram` component.

**Problem observed.** Two distinct failures, six weeks apart. First, `MermaidDiagram.jsx` was removed
from the frontend at `f488aac` (14 April) while the backend kept emitting Mermaid — leaving the
render agent producing output nothing consumed. `pbis/README.md` records the state bluntly: the
render agent "emits Mermaid that nothing consumes (`frontend/src/components/MermaidDiagram.jsx` is
never imported) — it is dead code." Second, layout that did survive fell through to
`positionMesh()` → dagre, a force-directed algorithm producing "inconsistent ('random') layouts
run-to-run".

**After.** `3314763` (20 June) deletes `mermaid_service.py`, `mermaid_ids.py` and
`MermaidDiagram.jsx`. `f7347e1` (21 June, PR #5) introduces the diagram template library: each
template is a Python definition plus a deterministic placement function emitting React Flow
`{id, type, position{x,y}, data{}}`. The backend supplies structure and positions; the frontend
keeps theme and styling only.

**Evidence it was an improvement.** The stated goal — "same repo in → same system diagram out, every
run" — is now measurable and **holds**: two consecutive pipeline runs on `django-helpdesk` produce
byte-identical `flow_graph.json` (§1.4 of `05_evaluation_inputs.md`).

### (f) Call-graph tracing → the decision algorithm

The central pivot. Documented in full in **`02_decision_algorithm.md`**.

### (g) `jarviscg` retired — a pivot the brief omits

**The brief presents (b) as the endpoint of call-graph tooling. It is not.** `jarviscg` was removed
entirely at `774102a` (16 July), and the design document states the reason in one line: *"jarviscg
fully retired (was 'optional cross-check')"* (`docs/decision_flow_tracer.md` v2 note 8).

**Why.** `jarviscg` "cannot supply call-site context" (§2, Stage 2). The decision algorithm depends
on knowing, for every call, which branch arm it sits under — and that is precisely what a
whole-program call graph discards. A second defect compounded it: `call_graph_service._to_serialisable`
collapsed the function-level graph to class→class edges using an "any uppercase segment" heuristic,
destroying function identity at the first stage.

**After.** `agents/tracer_agent/services/analysis/call_resolver.py` — a purpose-built layered
resolver producing `CallSite` records that carry the enclosing control context. The intermediate
"keep jarviscg as a cross-check, edges found by both resolvers are `confirmed`" position was
specified in the v1 design and dropped in v2 before implementation.

This pivot matters for the dissertation because it is the clearest case of an academically motivated
tool choice (Yan et al., 2023) being displaced by a project-specific requirement the literature did
not anticipate.

---

## 1.3 Dead ends and reversals

| What | Built | Removed | Why |
|---|---|---|---|
| `platform_orchestrator` agent | `6af8649`, 7 Apr | `78be90f`, 7 Apr | Nine files, removed the same day. Duplicated the `api/` gateway's orchestration role |
| `pyan3` | `45b0fc1`, 13 Apr | `7598d01`, 21 Apr | Superseded by `jarviscg` (pivot b) |
| Mermaid render path | initial | `f488aac` 14 Apr (frontend), `3314763` 20 Jun (backend) | Frontend component removed first; backend kept emitting unconsumed output for ~9 weeks |
| Five `shared/templates/*.json` | — | `5c3cea9`, 27 May | Forced every repository into one flat three-band layout |
| dagre / `positionMesh()` | — | PR #5, 21 Jun | Force-directed layout was nondeterministic run-to-run |
| Evaluation harness (`evaluation/`) | — | `f986fa0`, 15 Jul | "Stale, covered only module/edge recall." **Never rebuilt** — see below |
| `jarviscg` | 21 Apr | `774102a`, 16 Jul | Cannot supply call-site context (pivot g) |
| Evidence/critic–actor loop | `35df8ff`, 25 May | `774102a`, 16 Jul | Unnecessary once static analysis owned structure (pivot d) |
| Six placement templates (`hierarchy`, `hub_and_spoke`, `layered_tier`, `mesh`, `pipeline`, `relationship`) | PR #5, 21 Jun | `774102a`, 16 Jul | Shape became emergent from the graph rather than chosen per repo |
| `SequenceView.jsx` | `b9779cf`, 7 Aug | uncommitted working tree | Replaced by `FlowchartView.jsx` + 7 helpers. **Unfinished at time of writing** |

**The evaluation harness deletion is the most consequential reversal for the dissertation.** It was
removed on 15 July and `evaluation/` now contains only stale, untracked `__pycache__` files —
`git ls-files evaluation` returns nothing. The design document proposed a replacement ("a handful of
fixture repos with committed expected FlowGraphs — a plain snapshot test",
`docs/decision_flow_tracer.md` §6) which **was never built**. The project therefore has no automated
accuracy measurement over the period in which its core algorithm changed completely. This directly
affects LO5 and is treated at length in `05_evaluation_inputs.md`.

**A second, subtler reversal: the design document is partly superseded by what shipped.**
`docs/decision_flow_tracer.md` specifies "one page… **No drill-down**" (§ preamble) and "A node
budget **B** (~35) replaces drill-down" (Stage 6). The delivered system does the opposite: it uses
progressive disclosure with a 15-node skeleton and demotes rather than deletes
(`budget_config.py: skeleton_budget = 15`; `VisibilityBudgeter` "folds nothing away; it demotes",
`PROMPT.md` §8). The document was not updated to match. This is worth reporting honestly rather than
presenting the design as having been followed.

---

## Gaps and open questions

1. **No before/after measurements exist for pivots (a), (b) or (d).** Each is justified by reasoning
   in a design document, not by a recorded metric. A marker looking for empirical justification of
   the tooling changes will not find it. Closing this requires checking out the historical revision
   and running it against a fixture — feasible for (b) and (d), probably not for (a).
2. ~~Rules R1–R7 and W1–W5 are not in the repository.~~ **Closed.** Recovered from git; the set is
   R1–R6 (not R7) and W1–W5. Documented in `02_decision_algorithm.md` §2.1. Correct the count to
   **six** hard rules when writing the prose.
3. ~~The 3-iteration correction cap is unverified.~~ **Closed.** Confirmed at
   `tracer_service._correction_loop`: `for attempt in range(1, 4)`.
4. **PRs #9 and #10 are absent from `main`.** Whether they were closed unmerged or merged elsewhere
   cannot be determined locally. `gh pr view 9 --repo cooperkeenan/CodeFlow` would settle it.
5. **Commit messages are weak evidence for the early period.** Twelve commits between 11 April and
   11 July are titled "bug fixes", "working", "updated files" or "progress". LO1 (documentation and
   control) is better evidenced by `CLAUDE.md`, `PROMPT.md`, `pbis/` and `features/` than by the
   commit history, and the dissertation should lean on the former.
6. **The scoring weights have never been tuned.** `weight_reach=3.0`, `weight_provenance=2.0`,
   `weight_terminal=2.0`, `weight_dispatch_kind=1.0` were introduced at `5874f20` (16 July) and are
   unchanged since. `git log -p -- significance_config.py` shows two commits total. This is a real
   limitation, discussed in `02_decision_algorithm.md` §2.5.
7. **The interim report on disk is incomplete.** `~/Documents/Uni/Year_4/TR2/Honours_Project/Interim_Report.docx`
   contains only the literature review (§3.1–3.6, 4,512 words) — no objectives, no tech stack. Claims
   of the form "differs from what the interim report stated" cannot be checked. `~/Downloads/40595321.pdf`
   is presumably the full submission but has no text-extraction tool available on this machine
   (`brew install poppler` would enable it).
