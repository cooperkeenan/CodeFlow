# Understanding your own poster

Plain-English answers to the five questions, then a talk-track you can say out loud.

---

## 1. What do index, resolve and extract actually do?

These are the first three of the tracer's eight stages. All three are pure static
analysis — no model involved. Think of them as **read the words → work out who talks to
whom → find the places the code makes a choice.**

### Index (`project_indexer.py`) — build the phone book
Walk every `.py` file and parse it. Write down every function and method in the repo:
its full name, its file, its line numbers, its parameters.

It also has to work out what an import *means*. If `views.py` says
`from .forms import TicketForm`, index has to resolve `.forms` to a real file on disk.
It does that by walking the importing module's ancestor folders longest-first, so it works
for any directory layout — `agents/x/src`, `app/service/src`, whatever. It never assumes
a folder is called `agents` or `src`.

**Output:** a symbol table. "Here is every function that exists, and where it lives."

### Resolve (`call_resolver.py`) — join the dots
Now go through every function body and find every call. For each call, work out which
entry in the phone book it points at. `self.store.save(x)` → which class is `self.store`?
which `save` is that?

The important extra bit: it records the **control context** of each call — which branch
arm the call sits inside. So it doesn't just know "A calls B", it knows "A calls B *only
when the user is anonymous*". That context is what makes the decision diagram possible
later.

**Output:** the call graph. "Here is who calls whom, and under what condition."

### Extract (`dispatch_extractor.py`) — find the forks
Sweep the code for every place it can go more than one way. Seven detectors:

| Detector | What it catches |
|---|---|
| branch | `if` / `elif` / `else` |
| match | `match` statements |
| except | `try` / `except` — the error path is a real path |
| table | dict-of-handlers dispatch, `HANDLERS[kind]()` |
| route | URL → view mappings (Django URLconf, FastAPI decorators) |
| polymorphic | one call site, several subclass implementations |
| dynamic | `getattr`, plugin lookup — can't be resolved, so it's drawn as *dynamic* rather than guessed |

**Output:** a list of **candidate** forks. Thousands of them. Most are junk — that's the
next stage's problem.

> One line for the poster: *index says what exists, resolve says what calls what,
> extract says where it branches.*

---

## 2. How does the significance filter work?

The problem: a real repo has thousands of `if` statements and you can only show about
fifteen things on a page. Which ifs are worth drawing?

The filter answers that in **two passes: maths first, model second.**

### Pass 1 — deterministic ranking

**The core test is reach-set mutual exclusivity.** For each arm of the fork, compute the
set of functions that arm can reach. Then compare the sets.

```
if s is None:          →  arm A reaches {X, Y, Z}
    s = default            arm B reaches {X, Y, Z}
do_work(s)                 Same set. The arms rejoin. This is a GUARD.

if s == "cat":         →  arm A reaches {feed_cat, groom_cat}
    handle_cat()           arm B reaches {file_tax_return}
else:                      Different work. The arms do NOT reconverge.
    handle_tax()           This is a DECISION.
```

That's the whole intuition: **a guard checks a value and carries on; a decision sends the
system somewhere genuinely different.**

Each candidate then gets a score out of four terms (`site_scorer.py`, weights from
`significance_config.py`):

| Weight | Term | Why |
|---|---|---|
| **3.0** | `log2(1 + number of functions the arms reach)` | a fork governing lots of code matters more. `log2` so a fork reaching 200 functions isn't worth 100× one reaching 2 |
| **2.0** | provenance | is the thing being tested a **parameter** of the function (data flowing in from outside), rather than a local temp? scores 2 if the function is reachable from a web route, 1 if not, 0 if the test isn't on a parameter at all |
| **2.0** | fails to reconverge | the arms do not rejoin — the mutual-exclusivity test above |
| **1.0** | kind bonus | route / table / polymorphic dispatch is architectural by nature |

Two dampers before this: `utility_damper` discounts helper functions everything calls
(a logger reached from everywhere shouldn't inflate every score), and reach is capped at
depth 6 so it doesn't just swallow the whole repo.

### Pass 2 — the model verdict

Candidates are batched ~20 at a time to Haiku at temperature 0, and it answers three
things per fork:

1. **`decision` / `guarded_step` / `noise`** — is this worth drawing?
2. **The question a human would ask** — "User can access ticket?" rather than
   `if not request.user.is_authenticated`.
3. **An importance score** — used for final ordering.

Verdicts are cached on a content hash of the fork, so the same code always gets the same
answer and a re-run costs nothing.

**Result on the real cache: 5,916 forks judged → 63.4% guard, 9.3% noise, only 27.3%
decision.** Nearly three quarters are rejected before they reach the page. That number
*is* the contribution — the filter is the project.

**Say this if asked why you need a model at all:** the maths ranks, but it cannot tell
`if user.is_staff` (a real routing decision) from `if config.debug` (a guard) when both
score identically. And it certainly cannot write "User can access ticket?". Your own
`selfrun.py` shows the ablation: with the heuristic judge alone, guard-selectors survive.

---

## 3. Section 6 — what does "Grounding: 463/499" mean?

**Grounding = every box on the diagram can point at the exact line of code it came from.**

Each node carries a `SourceRef` — `file:line`. Click a node in the UI and it shows you
`public.py:230`. Figure 5 on the poster shows exactly this.

Why it matters: it's the anti-hallucination proof. A tool that hands the repo to an LLM
and asks for a diagram can produce a beautiful, confident, **fictional** component. Your
tool cannot, because a node only exists if static analysis found a real line of source to
attach it to. Grounding is the *measurement* of that claim.

**463 of 499 nodes carry a reference. The 36 that don't are all entry nodes** — a "web
entry point" isn't a single call site, it's the boundary where requests arrive, so there's
no one line to point at. That's by construction, not a miss. Which is why the poster says
so explicitly rather than quoting "93%" and hoping nobody asks.

> One line: *every box on the diagram is a line of code you can go and read.*

---

## 4. What are layout invariants?

Properties of the rendered diagram that **must be true on every run, for every repo** —
checked automatically by `scripts/flow_metrics.py`, which exits non-zero if any break.
They're the diagram's equivalent of unit tests.

The three on the poster, all **0** on django-helpdesk:

| Invariant | Means | Why it matters |
|---|---|---|
| **Overlapping boxes = 0** | no two node rectangles intersect | you can't read a diagram where boxes sit on top of each other. This is the one that catches layout regressions a screenshot hides |
| **Unreachable nodes = 0** (I2) | every node is reachable from the root by following edges | a node you can't reach by expanding is a node the user can never see. It's on the page but orphaned — a bug |
| **Cohesion violations = 0** (I5) | a node's children all belong to the same container; nothing is parented into two places at once | stops the containment tree tangling into a mess |

The point for a marker: **"it looked fine when I ran it" isn't evidence.** Counts and
screenshots both pass while a diagram is visibly broken. Invariants are automated checks
that fail loudly, so quality is asserted rather than eyeballed. Same discipline as
determinism — two runs, byte-identical output.

---

## 5. What are swim lanes?

A **swimlane** is a horizontal band in a diagram, one per actor, and every box sits in the
band of whoever performs it. Standard notation — borrowed from business process diagrams,
where you'd have a "Customer" lane, a "Warehouse" lane, a "Billing" lane, and an order
flowing left to right across all three.

In CodeFlow, **one lane per detected service**. On a self-run you get lanes for `api`,
`tracer`, `layout`, `render`, `profiler`, `scripts`, `figures`, `explain`.

Two things it buys you:

1. **Vertical position carries meaning.** You don't read a label to find out which service
   a step belongs to — you read its height on the page.
2. **Cross-service calls become visible.** When the gateway calls the tracer over HTTP, an
   edge crosses from one lane into another. Those are the **stitch** edges — `selfrun.py`
   asserts at least 4 of them. Normally an HTTP call is a dead end in static analysis (the
   trail stops at `httpx.post`); stitching matches the outbound URL to the route that
   serves it and joins the two halves, so a request that touches four services reads as
   one continuous journey instead of four disconnected diagrams.

Lanes are **detected**, not configured — derived from where imports actually resolve, so
it works on a repo laid out however its authors felt like laying it out.

---

# The script — how it all works, start to finish

Talk-track for standing at the poster. Roughly 90 seconds; each paragraph maps to a
numbered section.

---

**The problem.** Most of software work is reading code you didn't write, and the diagrams
that would help either don't exist or have rotted. Existing tools each fail differently:
comment-based generators need annotations nobody writes; PlantUML and Structurizr need a
human to author and maintain the diagram; hand the whole repo to an LLM and you get
something plausible and confidently wrong. **My aim: given only a repository, produce an
accurate, readable, single-page diagram of what the system does when it runs.**

**A user gives it a repo.** Sign in with GitHub, point it at a repository. Everything from
here is automatic.

**The profiler skims the shape of it** — modules, folders, where the service boundaries
are. It figures out how the project is laid out rather than assuming, because CodeFlow has
to work on repos with any directory structure.

**Then the tracer, which is the core, runs eight stages.**

*Index* parses every file and builds a symbol table — every function, where it lives,
what its parameters are. It also resolves imports properly, so it knows what `from .forms
import TicketForm` actually points at.

*Resolve* builds the call graph: who calls whom. And crucially it records the **branch arm
each call sits under** — not just "A calls B" but "A calls B only when the user is
anonymous."

*Extract* sweeps for every point the code can go more than one way. Seven detectors: if,
match, try/except, dict-dispatch tables, URL routes, polymorphic calls, and dynamic
lookups. On a real repo that's **thousands of candidates** — far more than fits on a page.

**So the decision algorithm decides which of those are real.** First deterministically: for
each fork, compute what each arm can reach and compare the sets. If the arms rejoin and
do the same work afterwards, it's a **guard** — `if s is None` — not something a person
would draw. If the arms reach materially different code, it's a **decision**. Then a score
weighted mostly on how much code the fork governs, whether the thing being tested came in
as a parameter, and whether the arms fail to reconverge.

**Then, and only then, a model.** It gets a *ranked list of forks that already exist* and
answers two questions: is this a decision or a guard, and what question would a human ask
here — "User can access ticket?" instead of `if not request.user.is_authenticated`.
Temperature zero, cached by content hash, and validated against ids the pipeline issued.
**It cannot add a node, remove one, or draw an edge.** That's the governing idea of the
whole project: *static analysis owns structure; the model judges significance and writes
labels.* Structural hallucination isn't unlikely — it's impossible by construction.

**Across 5,916 candidate forks it rejects nearly three quarters** — 63% guards, 9% noise,
27% real decisions.

**Condense and budget** turn what survives into the page. Decisions, their outcomes, the
effects they cause — database writes, HTTP calls, emails. Cross-service HTTP calls get
**stitched** so a request spanning four services reads as one journey. Then the budget:
django-helpdesk is a **394-node graph, and it opens as 18 nodes**. Nothing is deleted —
it's demoted a level, and every `+` expands to reveal what's underneath.

**Render places it.** Deterministic geometry, services as swimlanes, positions computed on
the backend — no auto-layout library guessing. And you get the flowcharts on the poster:
every box a real line of code, `file:line` on the node, click it and read the source.

**How I know it works.** Two full runs produce byte-identical graphs. 463 of 499 nodes
carry a source reference — the 36 without are entry points, which have no single call site
by construction. Zero overlapping boxes, zero unreachable nodes, zero cohesion violations,
checked automatically every run. **What I have not done** is a precision/recall study
against a human-labelled answer sheet, or a comparison against a baseline tool — so I make
no claim about accuracy. That's the top of the further work.

---
---

# Part 2 — follow-up questions

## 6. The tracer stages, one line each

Source of truth: `FlowPipeline.run()` in
`agents/tracer_agent/services/analysis/flow_pipeline.py`. The poster's Figure 1 compresses
this to eight labels; here is what actually executes, in order.

| # | Stage | Code | One line | Model? |
|---|---|---|---|---|
| 1 | **Index** | `ProjectIndexer` | Parse every file into a symbol table of functions, classes, parameters and spans; resolve imports to real files by walking ancestor prefixes. | no |
| 2 | **Resolve** | `CallResolver` | Build the call graph — who calls whom — recording the **branch arm** each call sits under. | no |
| 3 | **Extract** | `dispatch_extractor` | Find every candidate fork: branch, match, except, table, route, polymorphic, dynamic. | no |
| 4 | **Effects** | `EffectDetector` | Mark the calls that touch the outside world: db, http, llm, file, queue, email, response. | no |
| 5a | **Score** | `SignificanceFilter` → `SiteScorer` | Compute reach sets per arm, damp utility functions, and rank every candidate on the four-term score. | no |
| 5b | **Judge** | `LlmDecisionJudge` | Batch ~20 ranked forks per temperature-0 call: decision / guard / noise, plus the human question and an importance score. **The only structural-input model stage.** | **yes** |
| 6 | **Condense** | `flow_condenser` | Project the surviving decisions onto a `FlowGraph` of entry / step / decision / parallel / effect / outcome nodes, adding outcome nodes for arms that terminate. | no |
| 7a | **Entries** | `EntryFinder` | Find where requests actually arrive — route handlers, mains, CLI entry points. | no |
| 7b | **Stitch** | `FlowStitcher` | Match outbound HTTP calls to the routes that serve them so cross-service journeys join up. | mostly no¹ |
| 8a | **Rank** | `PillarRanker` | Score components on how central they are, which decides who gets page budget. | no |
| 8b | **Budget** | `VisibilityBudgeter` | Fold mergeable nodes, chain sequences, compute containment levels, and **demote** low-ranked nodes to a deeper level so the page opens at ≤15–18 nodes. Nothing is deleted. | no |
| 9 | **Name** | `FlowNaming` | Write human-readable labels for nodes, keyed to ids the pipeline already issued. | **yes** |
| 10 | **Review** | `FlowReviewing` | A model reads the finished graph and reports findings. It is asserted **not** to change node or edge counts (`selfrun.py` checks `pre=499n/698e post=499n/698e`). | **yes**, advisory only |

¹ `HttpStitchDetector` matches URLs deterministically; `LlmStitchDetector` only judges the
handful that URL matching cannot resolve.

**The line worth memorising:** of ten stages, seven are pure functions of the source tree.
The model judges (5b), names (9) and comments (10). It never adds, removes, merges or
rewires a node or an edge.

---

## 7. Is the layout agent still used?

**No — and this is worth knowing before a marker asks.**

The wiring is all still there: `LAYOUT_AGENT_URL` in `api/core/config.py`, a `LayoutClient`
built in `api/dependencies.py`, injected into `AnalysisService.__init__` as `self._layout`,
and a `layout` image still built by `scripts/build-push.sh`.

But `AnalysisService._run_from_profile()` **never calls it**. The live path is:

```python
trace = await self._tracer.trace(...)          # tracer returns flow_graph
flow_graph = trace["flow_graph"]
self._persister.write_json("layout.json", {"flow_graph": flow_graph})   # pass-through
diagram = await self._render.render(flow_graph)                          # straight to render
```

`layout.json` is written, but it is a verbatim copy of the tracer's output. `self._layout`
is a dependency that is stored and never used.

**Why:** the layout agent belongs to the V1 structural pipeline, where an LLM enriched
modules with tier/role/purpose labels. When the project became the V2 decision-flow tracer,
naming moved *inside* the tracer (`FlowNaming`, stage 9) — which is strictly better, because
there it is constrained to ids the pipeline issued. Leaving it as a live hop would have
handed a model the finished graph, which is exactly what the project argues against.

⚠️ **Poster accuracy note.** `figures/fig1_architecture.py` still draws
`("Layout", "POST /layout", ...)` as one of five agent services with a live arrow. That is
now inaccurate. Two honest options: drop the box, or keep it and grey it with the caption
"retained from the V1 pipeline; not on the current path". **Say the word and I'll change
it** — this is a five-minute fix and it is the kind of thing a second marker notices.

---

## 8. How does isolate work?

Isolate is the "zoom into one symbol" gesture — Figure 4 on the poster. On the map a node
is a box saying *what* happens; isolate answers *how it executes*.

**The gesture.** Click a node, press the isolate button (`IsolateButton.jsx`). The node
does not open a new page — it **grows into a frame in place**. `useIsolateAnimation.js` runs
a two-phase transition (dim 160 ms, expand 760 ms), `useIsolatedView.js` recomputes the
canvas so every other node is dimmed (`rf-dim`) and shifted outward (`spreadNodes`) to make
room, and the selected node scales up into a frame. Zoom is frozen during the animation so
the frame keeps a stable size. Press it again and it collapses back to a box.

**What's inside the frame** (`FrameContent.jsx`) — two panes:

*Left — the symbol.* `SymbolList` / `MethodList` / `HelperList` / `PrimarySummary`: the
class this node belongs to, every method on it, and the helper functions it calls. Each with
a one-line plain-English summary.

*Right — the flowchart.* `FlowchartView.jsx` draws the **control flow of the selected
method**: a proper flowchart, diamonds for conditions with Yes/No arms, boxes for calls,
terminators for returns and raises. `ViewToggle` swaps this pane for `CodeView` — the real
source, so you can go from picture to code without leaving the canvas.

**Where the flowchart data comes from — this is the important bit.** It is *not* generated
by a model and *not* computed in the browser. The tracer already built it, deterministically:

- `FunctionStepVisitor` (`agents/tracer_agent/.../function_step_visitor.py`) walks the
  method's Python AST and emits an ordered list of **steps**. `ast.If` → a decision step with
  arms, `ast.Match`, `ast.Try`, `ast.For` / `ast.While` → loop steps, `ast.Return` →
  a return step, `ast.Raise` → a raise step, everything else → the outermost calls in that
  statement. Nesting is capped at depth 4 and 40 steps per method, with the overflow shown
  honestly as a `+N more steps` node rather than silently dropped.
- `SymbolContextBuilder` bundles those steps with the source slice of every symbol the node
  touches, and ships it in the tracer's output. The frontend just lays it out
  (`flowchartLayout.js`, `flowchartPlace.js`, `flowchartWire.js` — measure, place, wire).

**Where the model comes in — labels only.** The `explain_agent` (`POST /explain`) takes an
`ExplainRequest` — the focus symbol, its methods, its helpers, and the step list — and
returns a `NodeExplanation`: a summary per method, a summary per helper, and a
`step_labels` map turning `if not request.user.is_authenticated` into "User is signed in?".
Haiku, temperature 0. Two validators police it: `ExplanationValidator` and
`StepLabelValidator` — the labels must key onto **step ids the tracer issued**, and a
`HeuristicSymbolExplainer` provides a deterministic fallback if the call fails or the
response fails validation.

So isolate is the same architecture as the main diagram, one level down: **static analysis
owns the shape of the flowchart; the model only writes what the boxes say.** That's a good
thing to point out at the poster — it shows the principle is applied consistently, not just
in the headline feature.

---

## 9. Where do the index and the call graph get stored?

**They don't. They are in-memory Python objects that die with the request.**

Look at `FlowPipeline.run()`: `index` and `callsites` are local variables passed from stage
to stage and then garbage-collected. There is no index database, no incremental cache of the
symbol table, no `.codeflow/` folder in the analysed repo. Every run rebuilds from source.

That is a deliberate trade, and a defensible one: an index that persists is an index that can
go stale, and staleness is precisely the failure mode the project exists to fix. Re-parsing
django-helpdesk is cheap next to the model calls.

What **is** persisted, and where:

| What | Where | Why |
|---|---|---|
| `profiler.json`, `tracer.json`, `layout.json`, `render.json` | local disk, via `OutputPersister` (`scratch_out/` or `shared/outputs/`) | the pipeline's stage outputs, for debugging and for the screenshot harness |
| `flow_graph.json` | same | the finished graph — the byte-identical determinism check compares two of these |
| Symbol context and step lists | **inside** `tracer.json` | so isolate has its flowcharts without re-analysing |
| LLM verdicts | `.cache/decision_verdicts.json` | content-addressed on the fork's source, so identical code always gets the identical verdict. Cold run on django-helpdesk ≈4 min; warm ≈3 s |
| Saved diagrams per user | **Neon Postgres**, `repo_maps` table | what you see when you log into the web UI |
| The repo's source | fetched per run (local path, or GitHub archive) | never retained |

So: **analysis is stateless and local; only results are stored.**

---

## 10. Is a "call graph" a real term?

**Yes — it's standard, textbook program-analysis vocabulary.** Use it without hedging.

A call graph is a directed graph where each node is a function and each edge means "this
function calls that one". It is the central data structure of interprocedural static
analysis, and it underpins compiler inlining, dead-code elimination, security taint
tracking, IDE "find all callers", and profilers.

The hard part is that it is **undecidable in general**. Given `handler.process(x)`, which
`process` runs depends on what `handler` is at runtime, and you can't always know statically.
So every call graph is an approximation, and the field is a spectrum of trade-offs from
cheap-and-imprecise (CHA — assume every subclass) to expensive-and-precise (points-to
analysis). Python is at the hard end: duck typing, `getattr`, monkey-patching, decorators.

**Two things you can say that show you know the literature:**

1. Your seven-detector split maps onto that problem directly. Six detectors resolve
   statically; `dynamic` is the honest escape hatch — a call it cannot resolve is **drawn as
   dynamic rather than guessed**. Under-approximating visibly beats over-approximating
   silently.
2. Your call graph carries something a plain call graph does not: **control context** — the
   branch arm each call sits under. A standard call graph says "A calls B". Yours says "A
   calls B only when the user is anonymous". That extra edge annotation is what makes a
   *decision* diagram possible rather than just a dependency diagram, and it's a fair thing
   to name as a contribution.

Related terms, so you're not caught out: a **control-flow graph** (CFG) is *within* one
function — the flowchart isolate draws is essentially a simplified CFG. A **call graph** is
*between* functions. You build both.
