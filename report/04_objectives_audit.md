# 04 — Objectives Audit

One subsection per interim-report objective: **Status**, **Evidence**, **Commentary**.

Objectives are reproduced as supplied. They could not be checked against the source document — the
interim report on disk contains only the literature review (§3.1–3.6) and states no objectives. See
"Gaps" below.

**Summary**

| # | Objective | Status |
|---|---|---|
| 1 | Three-agent pipeline, independent FastAPI microservices, validated schemas | **Delivered and exceeded** |
| 2 | JARVIS static call graph + LLM reasoning, grounded in deterministic evidence | **Superseded** — the goal was met by other means; JARVIS was removed |
| 3 | Interactive fractal drill-down frontend in React Flow | **Delivered** |
| 4 | Animated sequence diagram explorer synchronised with source code | **Not delivered** |
| 5 | RAG-based chatbot grounded in READMEs and source | **Not delivered** — never started |
| 6 | C4 model as structural framework across layers | **Not delivered** — abandoned with the layered pipeline |
| 7 | Qualitative semi-structured interviews across five roles | **Superseded and not yet executed** |

Three of seven delivered, two superseded, two not delivered. The commentary explains why that
summary understates the outcome: the work that displaced objectives 2 and 6 is the project's main
contribution.

---

## Objective 1 — Three-agent pipeline of independent FastAPI microservices

> *Design and implement a three-agent pipeline — Profiler, Tracer, Render — each an independent
> FastAPI microservice communicating through validated structured schemas.*

**Status: Delivered and exceeded.**

**Evidence.** Six services, not three: gateway (`api/`, 8000), profiler (8002), tracer (8003),
render (8004), layout (8006), explain (8007). Each is an independent FastAPI app with its own
`main.py`, `core/config.py`, `dependencies.py`, `routers/` and `models/`
(`agents/*/main.py`). Ports and URLs in `api/core/config.py`. Each agent exposes exactly one
endpoint. Deployment: `.github/workflows/cd.yml` builds six images and runs `railway redeploy` on
push to `main`.

Schema validation is genuine, not nominal. Every boundary is a Pydantic v2 model in `shared/models/`:
`RepoBlueprint` (profiler out), `TracerRequest` (tracer in), `FlowGraph` (tracer out, layout in/out,
render in), `RenderedView` (render out). `FlowGraph` additionally carries a
`model_validator(mode="after")` that sorts nodes and edges canonically — validation doing real work,
not just type-checking.

**Commentary.** The objective was met on its own terms and extended twice: the **layout agent**
(PR #4, 2 June) split archetype selection from placement, and the **explain agent** (8007) was added
to serve on-demand symbol summaries for the frame. The explain agent is architecturally the most
interesting addition because it is deliberately **outside** the pipeline — called by the gateway's
`NodeExplainService` only when a user opens a frame, so it costs nothing per analysis.

One caveat worth stating: the *services* are independent, but the *deployment* is not decoupled —
`cd.yml` redeploys all six on any push to `main` and is not gated on CI. Independent deployability,
usually a core motivation for microservices, is not exercised.

---

## Objective 2 — JARVIS static call graph integrated with LLM reasoning

> *Integrate static call graph analysis using JARVIS with LLM reasoning to produce diagram outputs
> grounded in deterministic structural evidence.*

**Status: Superseded.** The *stated goal* — outputs grounded in deterministic structural evidence —
is met more strongly than the objective required. The *stated mechanism* — JARVIS — was removed.

**Evidence.**

- JARVIS **was** integrated: `jarviscg @ git+https://github.com/nuanced-dev/jarviscg` in
  `requirements.txt` at `7598d01` (21 April), driven by
  `services/evidence/call_graph_service.py` (82 lines) as a subprocess with PyCG-format output
  conversion and an `entry_point_hint`.
- JARVIS **was removed** at `774102a` (16 July). `docs/decision_flow_tracer.md` v2 note 8:
  *"jarviscg fully retired (was 'optional cross-check')"*.
- The replacement is `services/analysis/call_resolver.py` plus `project_indexer.py` — a
  purpose-built layered resolver over the stdlib `ast` module.
- The remaining vestige is `entry_point_hint` in `shared/models/tracer_request.py`.

**Commentary — the honest account.**

This objective was **transformed, not missed**, and the transformation strengthened the objective's
underlying claim while invalidating its named tooling. Three things changed:

**1. JARVIS was removed for a concrete technical reason, not abandoned.** The decision algorithm
needs to know, for every call, *which branch arm it sits under*. A whole-program call graph discards
exactly that. `docs/decision_flow_tracer.md` §2 Stage 2: jarviscg "cannot supply call-site context".
A second defect compounded it — `call_graph_service._to_serialisable` collapsed the function-level
graph to class→class edges via an "any uppercase segment" heuristic, destroying function identity at
the first stage. The intermediate position ("keep it as a cross-check; edges found by both resolvers
are `confirmed`") was specified in the v1 design and dropped in v2 before implementation.

**2. The relationship between static analysis and LLM was inverted, in the objective's favour.**
The objective describes static analysis *integrated with* LLM reasoning. Under the pre-pivot design
the LLM **derived the structure** and static analysis served as evidence to check it against —
which is why `GraphValidator`, `EdgeRecovery` and a three-attempt correction loop existed. The
current design states the opposite as an invariant: *"static analysis owns structure; the LLM judges
significance and writes labels. The LLM may never add, remove, merge or rewire a node or edge"*
(`CLAUDE.md`, `PROMPT.md`, `HANDOFF.md`). "Grounded in deterministic structural evidence" is
therefore satisfied far more strongly than at the time the objective was written: the structure *is*
the deterministic evidence, rather than being checked against it.

**3. The grounding claim is now measurable, and it measures well.** Two consecutive runs on
`django-helpdesk` produce **byte-identical** `flow_graph.json`. 469 of 508 nodes on the self-run
carry a `SourceRef` with `file:line:end_line` (the 39 without are entries, which lack refs by
construction). `scripts/selfrun.py` asserts that node and edge counts are unchanged across the LLM
reviewer stage — **PASS**, `pre=508n/708e post=508n/708e`.

**But the objective is not fully met, and the dissertation should say so.** At `991bb11` (29 July)
the *survive-or-die verdict* moved from the deterministic `SiteClassifier` to `LlmDecisionJudge`. A
fork the model calls `noise` does not become a node. The LLM cannot invent a node, so the letter of
the invariant holds — but the **set** of nodes on the page is now model-determined, and run-to-run
stability rests on temperature 0 plus a content-addressed verdict cache rather than on the algorithm
being deterministic end-to-end. This is discussed at length in `02_decision_algorithm.md` §2.5(7).
Presenting the system as purely deterministic would overclaim.

**For the dissertation:** this is the strongest LO4 material in the project. An academically
motivated tool choice (Yan et al., 2023) was displaced by a project-specific requirement the
literature did not anticipate, and the displacement was justified in writing before it was made.
That is a defensible engineering decision documented at the time — which is exactly what critical
evaluation of process is supposed to surface.

---

## Objective 3 — Interactive fractal drill-down frontend in React Flow

> *Develop an interactive fractal drill-down frontend using React Flow allowing navigation at
> multiple levels of abstraction.*

**Status: Delivered.**

**Evidence.** `reactflow` ^11.11.4 (`frontend/package.json`). `frontend/src/pages/FlowPage.jsx` plus
`components/flow/` (FlowCanvas, NodeChrome, CameraController, ExpandToggle) and
`hooks/useExpansion.js`. Drill-down is driven by the backend `hidden_children` field: a node shows a
`+N` control when `hidden_children` is non-empty, and pressing it reveals exactly that list.
Measured on `django-helpdesk`: containment depth reaches **level 8** with 394 nodes, of which 16 are
always visible.

The first "fractal system" commit is `21d52bc` (14 April) — a system → module → component drill-down
on the old layered pipeline. The current progressive-disclosure model replaced it at `dd79a6a`
(4 August).

**Commentary.** Delivered, and the mechanism is better than the objective implies. The original
"fractal" model had three **fixed** abstraction levels (system, module, component). The delivered
model has no fixed levels: `level` is computed by BFS over the containment relation
(`ContainmentIndexer._assign_levels`) and goes as deep as the code does. `CLAUDE.md` states the
governing constraint — *"The first thing shown is the whole codebase at a high level: max 15 nodes.
Detail is not deleted to achieve this — it is demoted to a deeper visibility level."*

Two honest qualifications:

- The skeleton **overshoots its own budget**: `flow_metrics.py` reports `skeleton (lvl 0) 16
  (budget 15)`.
- The top-level page is thin. Reading `scratch_out/flow.png` directly: eleven disconnected entry
  ovals in a row, one three-node chain, two isolated nodes. Zero overlaps and within budget, but as a
  navigable mental model it reads closer to a list of entry points than to a connected picture.
  `HANDOFF.md` §6 lists this as a known open defect. **Node counts and invariant checks all pass on
  this diagram, which is precisely why they are not sufficient evidence of quality.**

An addition not in the objective: the **frame** (isolate). Clicking a revealed node's isolate control
grows that node to ~92% of the canvas and fills it with the symbol behind it — file, class/function,
methods with plain-English summaries, and a code/flowchart toggle. This is a fourth navigation level
that the objective did not anticipate.

---

## Objective 4 — Animated sequence diagram explorer synchronised with source

> *Develop an animated sequence diagram explorer synchronising a step-through sequence diagram with
> the corresponding source code.*

**Status: Not delivered.**

**Evidence.** Three findings, in order:

1. **No sequence-diagram explorer exists in the delivered system.** `git log -S'SequenceDiagram'`
   returns only the initial commit (7 April), where it was removed as an ignored file.
   `shared/models/diagram_template.py` declares nine `DiagramType` values; `sequence` is not among
   them. `pbis/README.md` lists `sequence` explicitly as a **deferred drop-in**: *"(`sequence`,
   `state_machine`, `event_flow` are deferred drop-ins.)"*
2. **The closest thing built was `SequenceView.jsx`** (`b9779cf`, 7 August), a 57-line component in
   the frame. Reading it: it renders a **static tree of call order** — caller heading, then rows of
   `├─ line 412 ▶ methodName` — from a `sequence` prop. It is not animated, has no step-through, and
   does not synchronise with a source view. Its empty state reads *"no call sequence recorded for
   this class"*.
3. **It has since been deleted.** `SequenceView.jsx` is deleted in the uncommitted working tree and
   replaced by `FlowchartView.jsx` plus seven `flowchart*` helper modules. The frame's `ViewToggle`
   now offers `code` and `flow` (`data-testid="view-code"` / `"view-flow"`) — the sequence option is
   gone.

**Commentary.** Give this a straight answer in the dissertation: **the animated sequence diagram
explorer was not built.** A static call-order list existed inside the frame for roughly one day and
was replaced by a flowchart view.

The substitution is defensible on the project's own logic and should be argued rather than
apologised for. A sequence diagram is a *temporal* view of call order — which is, precisely, the
structural-enumeration representation the project's central thesis rejects. The flowchart view shows
the selected method's **steps and branches**, which is the decision abstraction applied at method
scope. Replacing the sequence view with the flowchart view is the same pivot as §2, applied one
level down.

What is genuinely delivered against the *spirit* of the objective — synchronising a visual view with
the corresponding source — is the frame's code view: selecting a method shows its real source,
served by `POST /repomaps/{repo}/explain` with `file:line` provenance. Step-through animation is not
delivered.

**Note the risk:** `FlowchartView.jsx` and its seven helpers are **untracked and uncommitted** at
time of writing. If the dissertation cites the flowchart view, commit it first.

---

## Objective 5 — RAG-based chatbot grounded in READMEs and source

> *Implement a RAG-based chatbot grounded in repository README files and source code.*

**Status: Not delivered. Never started.**

**Evidence.** A straight answer, with the searches that support it:

- `grep -ril chatbot` across the working tree: **zero hits.**
- `git log --all -S'chatbot'`: **zero commits.**
- No vector store, no embedding model, no retrieval component, no chat endpoint. The gateway's
  endpoint list contains nothing conversational.
- No vector-database dependency in `requirements.txt` at any revision.
- The only "embeddings" hits in history are in documents **ruling the approach out**:
  `pbis/README.md` states *"there are no embeddings/vector DBs"* as a locked decision.

**Commentary.** This is the clearest not-delivered objective, and the repository shows it was
deliberately excluded rather than run out of time on. The project's recorded design position is that
retrieval over embedded text is the wrong tool for this problem: the governing principle is
deterministic static analysis with the LLM confined to judging and naming, and a RAG chatbot is the
opposite — nondeterministic retrieval feeding unconstrained generation.

The dissertation should state plainly that the objective was dropped, and give the reason, which is
on the record in `pbis/README.md` and `CLAUDE.md` rather than being constructed after the fact.

There is one honest complication: the **explain agent** (8007) is arguably the need this objective
was reaching for — plain-English explanation of code, on demand, grounded in the repository. It is
not RAG and not a chatbot: it is given exact source slices selected by `SymbolContextBuilder` via the
FQN in `flow_graph.meta.symbol_context`, with results cached by content-addressed fingerprint. That
is retrieval by *static resolution* rather than by *embedding similarity* — a defensible alternative
answer to the same question, and worth presenting as such.

---

## Objective 6 — C4 model as a structural framework across layers

> *Apply the C4 model as a structural framework for representing architecture across layers.*

**Status: Not delivered.**

**Evidence.** No C4 vocabulary survives anywhere on the live path. The C4 levels — Context,
Container, Component, Code — do not appear as node kinds, view types or model fields.
`FlowGraph.NodeKind` is `entry | step | decision | parallel | effect | outcome`; the nine
`DiagramType` values in `diagram_template.py` are layout archetypes (`pipeline`, `hub_and_spoke`,
`layered_tier`, …), not C4 levels. `grep -ril C4` returns only incidental hex-colour and identifier
matches. The interim report's literature review discusses the C4 model at length (§3.5, "The C4 Model
and Multi-Level Abstraction"), so the intent was real.

The nearest realisations, both abandoned:

- The layered `DiagramSpec` (`presentation` / `business` / `data`) is a three-tier model, not C4;
  `layers` was itself replaced by `modules`/`zones` and the file is now dead code.
- The system → module → component drill-down (`21d52bc`, 14 April) maps loosely onto C4's
  Container → Component → Code, and was removed at the pipeline cut-over (`774102a`).
- `ExternalActor` (`database | api | webhook | browser`) is the one surviving C4-flavoured concept
  — the external systems of a Context diagram — and it lives in the dead `diagram_spec.py`.

**Commentary.** C4 was superseded by the same pivot as objective 2, for a reason the dissertation can
state directly: **C4 is a decomposition of a system into nested structural containers, which is the
representation the project's thesis argues against.** Applying C4 would have meant committing to
exactly the "faithful representation of the code, poor representation of understanding" that
motivated the decision algorithm.

What replaced it is genuinely a multi-level abstraction — containment depth computed from the code
rather than assigned to four fixed tiers, reaching level 8 on `django-helpdesk`. The objective's
*purpose* (representing architecture across levels of abstraction) is met; its *named framework* is
not used.

The literature review will need adjusting: §3.5 motivates C4 as the structural framework, and the
delivered system does not use it. That mismatch is better addressed explicitly in the evaluation
chapter than left for a marker to notice.

---

## Objective 7 — Qualitative semi-structured interviews across five roles

> *Evaluate effectiveness through qualitative semi-structured interviews across five roles.*

**Status: Superseded in methodology, and not yet executed.**

**Evidence.** The ethics application
(`~/Documents/Uni/Year_4/TR2/Honours_Project/Ethics_Form_CodeFlow_COMPLETED.docx`, completed
28 July 2026, 1,879 words) documents a **different method** from the objective:

| | Objective (interim report) | Ethics form (approved method) |
|---|---|---|
| Method | Semi-structured interviews | *"A single anonymous online questionnaire (Microsoft Forms)"* |
| Sampling | Five roles | *"Approximately 8–12 adult (18+) software developers and computing students"* |
| Analysis | Qualitative | *"analysed descriptively: counts of correct, missing and incorrect diagram elements, median Likert ratings, and thematic grouping of free-text comments"* |
| Setting | — | *"Online — participants use the web tool and complete the questionnaire remotely"* |
| Duration | — | ~30 minutes |
| Project window | — | Start 4 August 2026, *"complete by 14 August 2026"* |

The form answers "No" to all fourteen risk-screening questions, requiring Section 3a only. Its design
is well matched to the research question: participants *"nominate an open-source repository they
wrote or know well"* and grade whether *"the entry points [are] correct, are the decision points
shown genuine, has anything significant been missed, and does anything shown not actually exist in
the code."* That final pair is a recall/precision framing over the diagram, obtained from someone who
knows the ground truth.

**What does not exist:**

- **No questionnaire instrument.** No Microsoft Forms export, no question list, no draft, in either
  the repository or the project folder.
- **No completed participant information sheet.** `~/Downloads/Information sheet and consent form.docx`
  is the **unmodified university template** — `[INSERT CONTEXT]`, `[INSERT METHOD(S) AND CONTEXT]`
  and `[INSERT YOUR NAME & CONTACT]` are all still placeholders. The ethics form commits to attaching
  this sheet to every invitation.
- **No responses, no participants, no results.**
- The ethics form itself carries two unresolved placeholders: `[Napier student email — TO CONFIRM]`
  and `[Contact number — TO CONFIRM]`.

**Commentary.** Two separate things to report, and they should not be conflated.

**The methodology change is defensible and should be presented as a considered decision.** Five-role
semi-structured interviews would produce impressions of a diagram from people who mostly cannot
verify it. The questionnaire design instead recruits participants who know a codebase well enough to
judge correctness, and asks them to count what is right, missing and fabricated. That is a shift from
measuring *perceived usefulness* to measuring *accuracy against ground truth held by the
participant* — a stronger design for LO5, and it directly addresses the project's central weakness
(§`05_evaluation_inputs.md`: there is no automated accuracy measurement at all). Recruiting 8–12
participants is also more realistic than five role-stratified interviews.

**The execution risk is severe and time-critical.** As of 8 August 2026 the study has not started.
The ethics form's own completion date is 14 August 2026 — the dissertation deadline. Delivering it
requires, in order: filling the participant information sheet (currently a blank template), building
the Forms instrument, recruiting 8–12 participants, allowing ~30 minutes each, and analysing the
results. **This is the single largest risk to the dissertation's LO5 mark and it is the one item in
this evidence pack that is worth acting on immediately.**

If the study cannot be run in time, the fallback with the best evidence-to-effort ratio is the
with-LLM/without-LLM comparison described in `02_decision_algorithm.md` §2.4 — one command, isolating
one variable, on a repository that is not CodeFlow.

---

## Gaps and open questions

1. **The objectives could not be verified against the interim report.** `Interim_Report.docx` on disk
   holds only the literature review. The wording above is as supplied in the brief. If the submitted
   PDF phrases any objective differently — particularly 2 and 4 — the status calls could shift.
   `brew install poppler` would make `~/Downloads/40595321.pdf` readable.
2. **"Five roles" is unexplained.** Which five roles objective 7 intended is not recorded anywhere
   available, so it cannot be assessed whether the 8–12 developer sample covers them.
3. **Whether ethics approval was formally granted is not evidenced.** The form is completed; no
   approval confirmation, reference number or supervisor sign-off was found. It also still contains
   two `TO CONFIRM` placeholders.
4. **Objective 4's status could change if the flowchart view is presented as the deliverable.** That
   is a legitimate reframing, but `FlowchartView.jsx` and its seven helpers are currently untracked.
   Commit them before citing them.
5. **No artefact records *when* objectives 5 and 6 were dropped.** Both are absent rather than
   removed, so there is no commit to point at. The reasoning reconstructed above comes from
   `pbis/README.md`, `CLAUDE.md` and `docs/decision_flow_tracer.md`, which state the principles but
   never say "objective 5 is cancelled". A supervisor meeting record, if one exists outside the
   repository, would be better evidence.
