# 02 — The Decision Algorithm

The intellectual core of the project: the change from representing a codebase as a graph of
*structural* relationships (A imports B, X calls Y) to identifying and ranking the **decision points**
a developer actually holds in their head.

This document is written to be precise enough that an examiner could reimplement the algorithm from
it. Every constant, threshold and class name is quoted from the source at commit `b9779cf` unless
stated otherwise.

---

## 2.1 What it replaced

### The mechanism

The pre-pivot tracer (25 May – 16 July 2026) was an **LLM-derived structure** pipeline. Static
analysis produced evidence; the LLM produced the graph. Six services, all deleted at `774102a`:

| File (at `774102a^`) | Lines | Role |
|---|---|---|
| `services/evidence/call_graph_service.py` | 82 | Ran `jarviscg` as a subprocess, converted PyCG-format output, threaded `entry_point_hint` |
| `services/evidence/ast_service.py` | 137 | `_extract_calls` walked the tree emitting bare callee names; `extract_signatures`, `build_import_graph` |
| `services/evidence/evidence_service.py` | 64 | Assembled `confirmed_edges` / `import_edges` / `call_edges` / `signatures` into the LLM's evidence bundle |
| `services/tracing/tree_traversal_partitioner.py` | 96 | Chunked the class-level graph for the LLM |
| `services/tracing/chunk_tracer.py` | 71 | Per-chunk LLM call (Haiku) producing components and edges |
| `services/tracing/correction_prompt_builder.py` | 66 | Re-prompted the LLM with its own validation failures |
| `services/assembly/graph_validator.py` | 136 | Checked the returned `DiagramSpec` against the evidence |
| `services/assembly/raw_merger.py` | 55 | Merged per-chunk results |
| `services/assembly/edge_recovery.py` | 14 | Re-added evidence edges the LLM dropped |

Control flow: index → `jarviscg` call graph → collapse to class→class edges → partition into chunks →
one LLM call per chunk producing components and edges → merge → validate → up to **three** correction
re-prompts → `DiagramSpec`.

### The validation rules, recovered

The brief refers to "rules R1–R7 and warnings W1–W5". The actual rule set, recovered from
`git show 774102a^:agents/tracer_agent/services/assembly/graph_validator.py`, is **R1–R6 and W1–W5**
— there is no R7. The auto-fix / re-prompt split the brief asks about is a three-way split, and it is
explicit in the code:

**Hard rules — applied deterministically, never sent to the LLM** (`_apply_hard_rules`, recorded as
`errors`):

| Rule | Action |
|---|---|
| R1 | Remove edge whose source or target is not a known component |
| R2 | Remove `entry_point` not present in any layer |
| R3 | Remove `child` reference to an unknown component |
| R4 | Remove duplicate edge (same source, target, `edge_type`) |
| R5 | Remove self-edge |
| R6 | Strip empty `io` entry from a component |

**Correctable warnings — fed back to the LLM** (`correctable` list → `CorrectionPromptBuilder`):

| Warning | Meaning | Prompt section |
|---|---|---|
| W1 | Component has no incoming or outgoing edges | "ORPHANED COMPONENTS" |
| W2 | An edge confirmed by *both* import and call analysis is missing from the spec | "CONFIRMED EDGES FROM EVIDENCE" |
| W5 | Component lists a child but no corresponding edge exists | "MISSING EDGES" |

**Non-correctable warnings — reported only** (`warnings` list):

| Warning | Meaning |
|---|---|
| W3 | Edge present in the spec but not in the evidence |
| W4 | Component has empty `io` but public methods with parameters |

**Why the split was made.** The three correctable warnings are all *omissions* — the model left
something out that the evidence says should be there, and asking for it back is a well-posed
request. R1–R6 are *violations of the schema's own consistency*, which the code can repair without
consulting anyone; sending them to a model would risk it changing something else. W3 and W4 are
neither: W3 flags an edge the evidence cannot confirm, which may be a true edge the static analysis
missed rather than a hallucination, so removing it automatically would lose real information and
re-prompting would invite the model to argue. W4 is advisory.

The loop is capped at three attempts — `for attempt in range(1, 4)` in
`tracer_service._correction_loop`, with the prompt itself stating "This is correction attempt
{attempt} of 3" and a warning logged when the cap is reached with warnings unresolved.

### A real "before" output

Recovered from `git show b40216f:shared/outputs/tracer_output.json` (14 April 2026, 12,905 bytes).
Note this is a **web-scraper repository**, not `django-helpdesk` — see §2.4.

```
architecture_type: "three-tier"
layers.presentation:  2 components  [ScraperAPI, SessionExecutor]
layers.business:     13 components  [ScrapingOrchestrator, MarketplaceScraper, MatchingEngine,
                                     ProductService, BrowserService, FacebookService, SessionService,
                                     ProxyService, TitleMatcher, PriceMatcher, KeywordFilter,
                                     ConfidenceCalculator, BrowserHelper]
layers.data:          5 components  [ProductRepository, ListingRepository, Product, Listing, MatchResult]
TOTAL: 20 components, 24 edges, 1 entry point, 5 external actors
```

Each component carried `name`, `description`, `file_path`, `io.inputs`/`io.outputs`, `children`.

---

## 2.2 The failure mode being addressed

Not "it was inaccurate". Four specific structural failures, each named with the function responsible
in `docs/decision_flow_tracer.md` §1:

**1. Class-level collapse.** `call_graph_service._to_serialisable` reduced `jarviscg`'s
function-level graph to class→class edges using an "any uppercase segment" heuristic. Function
identity — *where decisions actually live* — was destroyed at the first stage and was never
recoverable downstream. Module-level functions, `main()` entry points, and same-named classes in
different packages were all mangled into the same bucket.

**2. Flat call extraction.** `ast_service._extract_calls` walked the whole tree and emitted bare
callee names. Which function a call lives in, which branch arm it sits under, whether it is inside a
loop or an `except` — all discarded. The design document's verdict: this context "is the single most
important thing the old pipeline threw away."

**3. LLM-derived structure.** The chunk/breadcrumb/merge sequence asked the model to guess components
and edges from signatures. "The structure the LLM is guessing is exactly what static analysis can
compute deterministically. The chunk boundaries, breadcrumb summaries, and merge step each add loss
and nondeterminism; `GraphValidator` and `EdgeRecovery` then try to patch the result back toward the
facts." The correction loop was a symptom, not a feature.

**4. Wrong entry-point model.** Root detection used "no incoming edges", which misses framework entry
points entirely. In a FastAPI or Django codebase the routers *are* the entry points and nothing calls
them statically.

### What the diagrams over- and under-represented

Reading the recovered output against these failures:

- **Over-represented: data-holding classes.** Five of twenty components (`Product`, `Listing`,
  `MatchResult`, and the two repositories) are storage or value types. They occupy a quarter of the
  diagram and contain no behaviour a reader needs to reason about.
- **Over-represented: fan-out breadth.** `SessionExecutor` lists five children and
  `ScrapingOrchestrator` three, producing a wide shallow tree that restates the constructor-injection
  graph. This is the codebase's *wiring*, redrawn.
- **Under-represented: every choice the system makes.** The word "if", the concept of a branch, and
  any notion of alternative paths are absent from the entire 12,905-byte output. `MatchingEngine`
  "matches scraped listings to products using multiple matching strategies" — the strategies are
  named as sibling components (`TitleMatcher`, `PriceMatcher`, `KeywordFilter`) but **which one runs
  when, and on what basis, is not represented at all.** That selection is the architecturally
  significant fact, and the diagram cannot express it.
- **Under-represented: entry points.** One entry point (`ScraperAPI`) for an entire HTTP API. Per
  failure 4, individual routes were invisible. The current pipeline finds **33 entries** in
  `django-helpdesk`.

This is the thesis in concrete form: enumerating call and containment edges reproduces the codebase
in a different notation. The 20-component diagram is a faithful and largely useless picture — it
answers "what classes exist and which hold references to which", a question the reader could answer
from the directory listing.

---

## 2.3 The algorithm

Composed by `agents/tracer_agent/services/analysis/flow_pipeline.py` (`FlowPipeline.run`, 118 lines).
Eight stages. Stages 1–4 and 6–8 are pure functions of the source tree; stage 5 is the only
model-driven step.

### 2.3.0 The definition of a decision node

The unit is not "an if statement". It is a **dispatch site**: any point where one caller may invoke
one of N alternatives. The taxonomy is enumerated by `build_dispatch_extractor`
(`dispatch_extractor_factory.py`) as seven detectors, and typed as
`DispatchKind = Literal["branch", "match", "table", "route", "polymorphic", "except", "dynamic"]`
(`models/dispatch_site.py`):

| Kind | Detector | Source of divergence | Arms |
|---|---|---|---|
| `branch` | `BranchDetector` | `if / elif / else`, ternary, `and`/`or` | CFG arms of the statement |
| `match` | `MatchDetector` | `match / case` | case arms |
| `except` | `ExceptDetector` | `try / except` with a fallback path | try arm + each except arm |
| `table` | `TableDetector` | dict-of-callables / registry lookup + call | the dict's key→value entries |
| `route` | `RouteDetector(FastApiRouteScanner, DjangoRouteScanner)` | framework route tables | one arm per registered route |
| `polymorphic` | `PolymorphicDetector` | call through a base-type annotation | overriding implementations (**≥2 required** — single-implementation polymorphism is indirection, not a decision) |
| `dynamic` | `DynamicDetector` | `getattr` with a computed name, exec-time lookup | **unresolvable — rendered honestly, never guessed** |

The design rationale for this taxonomy is worth quoting because it is a genuine insight and defends
against an obvious objection:

> "the better a codebase follows Open/Closed, the more its decisions live in tables, routes, and
> polymorphism rather than `if` ladders. **A branch-only detector works worst on the best
> codebases.**" — `docs/decision_flow_tracer.md` §2

The record produced is:

```python
@dataclass(frozen=True)
class DispatchSite:
    id: str                 # stable: "{owner_fqn}:{line}"
    owner: str              # FQN of the enclosing function
    kind: DispatchKind
    selector_source: str    # the condition/key/type expression, verbatim
    selector_reads: tuple[str, ...]   # names the selector reads — used for provenance scoring
    arms: tuple[Arm, ...]
    reconverges: bool       # do the arms rejoin within the owner function?
    span: SourceRef

@dataclass(frozen=True)
class Arm:
    index: int
    label_source: str
    callsites: tuple[CallSite, ...]
    terminal: Literal["returns", "raises", "continues", "falls_through"]
    handler_fqn: str | None = None
```

### 2.3.1 Stages 1–2: Index and Resolve (deterministic)

`ProjectIndexer.index(files)` parses every file once with `ast` and builds a symbol table: module FQN
→ classes, functions, methods; per-module import bindings; per function its qualified name,
annotated parameters, return annotation and source span.

Imports resolve by **walking the importing module's ancestor prefixes longest-first**
(`path_fqn.py`), with stdlib names short-circuiting the walk. Source roots are derived from where
imports actually bind — not from directory names. This is a corrected defect, not an original design
choice: `path_fqn.agent_root_of` originally keyed on the literal string `"agents"`, so on a repo laid
out as `app/<service>/src` nearly every internal call resolved to `ext:` and the call graph was
shredded (`CLAUDE.md`; fixed at `fec2828`).

`CallResolver(index).resolve_project()` then resolves every call expression through a layered
resolver, emitting a `CallSite` carrying caller FQN, target(s), line and — critically — its
**control context**: the stack of enclosing control constructs (dispatch-site id + arm index), loop
flag, and try/except arm. Resolution order:

1. bare name → local scope, then import bindings;
2. `self.x()` / `cls.x()` → own class, then MRO (`mro_method_finder.py`);
3. `self._dep.x()` where `_dep` was assigned from an annotated `__init__` parameter → the
   annotation's type (`dependency_param_mapper.py`, `attr_type_collector.py`). Constructor injection
   plus mandatory annotations makes this the workhorse resolver;
4. annotation is a base type with ≥2 concrete overriders → resolve to **all** implementations and
   record a `polymorphic` site (`subclass_index_builder.py`, `protocol_implementation_resolver.py`);
5. otherwise → `dynamic`: recorded and counted, never guessed.

Confidence is graded `resolved` / `inferred` / `dynamic` so untyped codebases degrade gracefully
rather than going dark.

### 2.3.2 Stages 3–4: Extract and score candidates (deterministic)

`build_dispatch_extractor(index).extract(callsites)` runs the seven detectors in fixed order and
concatenates their sites. `EffectDetector.detect` separately finds I/O boundaries
(http / db / llm / file / queue / email / response).

`SignificanceFilter.run(callsites, sites)` then computes, in order:

**(a) Utility damping.** `UtilityDamper.compute` identifies high fan-in helper components, which are
excluded from reach sets so that "both arms call the logger" does not make two arms look alike.
Thresholds: `utility_min_fan_in = 8`, `utility_percentile = 0.90`.

**(b) Reach sets.** `ReachComputer.arm_reach(arm, owner_component)` computes the set of project
components transitively reachable from an arm's callees, over an SCC-condensed call graph, bounded at
`reach_max_depth = 6`.

**(c) Arm classification.** `ArmClassifier.classify(arm, reach)` — a three-way, purely deterministic
label:

```python
if arm.terminal in {"raises", "returns", "continues"} and len(reach) <= guard_reach_limit:  # 2
    return "guard"
if not reach:
    return "void"
return "live"
```

**(d) Heuristic score.** `SiteScorer.score(site, live_union)` — the ranking function, with the weights
exactly as they appear in `significance_config.py`:

```
score = weight_reach       · log₂(1 + |live_union|)      # 3.0
      + weight_provenance  · provenance(site)            # 2.0 × {0, 1, 2}
      + weight_terminal    · (0.0 if site.reconverges else 1.0)   # 2.0
      + weight_dispatch_kind · (1.0 if kind ∈ {route, table, polymorphic} else 0.0)  # 1.0
```

where `live_union` is the union of the reach sets of arms classified `live`, and

```python
def _provenance(site):
    if no name in site.selector_reads is a parameter of the owner function:  return 0
    return 2 if route_reach.is_route_reachable(site.owner) else 1
```

That is: a fork whose condition tests a parameter of a function reachable from an HTTP route scores
2; a fork testing any other parameter scores 1; a fork testing internal state scores 0. The intuition
is that decisions driven by external input are more architecturally significant than decisions driven
by local bookkeeping.

The reach term is **logarithmic**, so a fork reaching 100 components is not fifty times more
important than one reaching 2. This is deliberate damping of a metric that would otherwise be
dominated by whichever arm happens to call into a large subsystem.

### 2.3.3 Stage 5: Judge (the only LLM stage)

This is where the design changed most between the specification and what shipped. The design
document assigned the LLM **labelling only** (`docs/decision_flow_tracer.md` Stage 7: "the LLM only
names things", "hallucination is impossible by construction"). The delivered system also gives the
LLM the **significance verdict** — `991bb11`, 29 July, "Judge forks with an LLM instead of a reach
heuristic".

`DecisionJudge` is a `Protocol` with two implementations, selected by
`decision_judge_factory.build_decision_judge`:

**`HeuristicDecisionJudge`** — the deterministic default when no API key is present. Delegates to
`SiteClassifier.classify`, which is the divergence gate as originally specified:

```python
if kind in {"route", "table", "polymorphic"} or kind == "dynamic":
    return "decision" if len(arms) >= 2 else "noise"
if kind in {"branch", "match", "except"}:
    live = [reach for arm, reach in ... if arm_class == "live"]
    if len(live) >= 2 and mutually_exclusive(live):   # no reach set is a subset of another
        return "decision"
    if len(live) == 1 and any(cls == "guard" for cls in arm_classes):
        return "guarded_step"
    return "noise"
```

A null-guard fails automatically: its guard arm raises or returns early and reaches nothing. A router
passes automatically: each arm reaches a different handler. **No semantic judgement is involved.**

**`LlmDecisionJudge`** — the production path. Batches **20** candidates per call to
`claude-haiku-4-5-20251001` at **temperature 0**, returning per site a verdict of
`decision` / `guard` / `noise`, a 2–6 word `question`, `arm_labels`, `confidence` and an `importance`
in [0,1]. The system prompt (`prompts/decision_judge_prompt.py`, `PROMPT_VERSION = "2"`) defines a
decision as "a branch point where the program chooses between genuinely different courses of action
that a reader would need to know about", and explicitly excludes null checks, input validation,
logging, formatting, caching, retries and trivial defaulting.

The evidence sent per candidate is deliberately narrow — `id`, `where` (`file:line`), `kind`,
`enclosing_function`, `arm_reach_sizes`, and a source snippet capped at `_MAX_SNIPPET_LINES = 25`.

**Failure handling is layered, and this matters for the determinism claim:** a batch that raises
falls back to `HeuristicDecisionJudge`; individual entries that fail to parse fall back likewise;
only successfully parsed verdicts are cached.

**Caching.** `VerdictCache` is content-addressed on a fingerprint of the fork's source, arm labels
and reach sizes plus `PROMPT_VERSION` (`decision_fingerprint.py`), persisted to
`.cache/decision_verdicts.json`. Identical forks share one verdict — the judge deduplicates by
fingerprint before calling, sending only one representative per group. Cold run on
`django-helpdesk` ≈4 min; warm ≈3 s.

### 2.3.4 Where the LLM sits versus deterministic code

| Stage | Owner | Rationale |
|---|---|---|
| 1 Index, 2 Resolve, 3 Extract, 4 Score | Deterministic | Structure is computable; a model guessing it adds loss and nondeterminism |
| **5 Judge** | **LLM** (heuristic fallback) | Whether a fork is *architecturally significant* is a semantic judgement the reach heuristic provably could not make — see §2.5 |
| 6 Condense, 7 Stitch (URL matching), 8 Budget | Deterministic | Graph construction |
| 7 Stitch (unresolvable) | LLM (`LlmStitchDetector`) | Only where URL matching cannot resolve a match |
| Labelling (`FlowNamer`) | LLM | Cosmetic; `llm_label` is a separate field from `label` |
| Review (`FlowReviewer`) | LLM | Advisory findings only |

The invariant, stated in `CLAUDE.md`, `PROMPT.md` and `HANDOFF.md` alike: **the LLM may never add,
remove, merge or rewire a node or edge.** This is enforced structurally — the judge returns a verdict
keyed to a site id the pipeline issued, and `FlowNamer` writes only into `llm_label`/`one_liner`
fields. `scripts/selfrun.py` asserts it directly: *"node/edge counts unchanged across reviewer stage:
pre=508n/708e post=508n/708e"* — **PASS**.

### 2.3.5 Stages 6–8: Condense, stitch, budget (deterministic)

**Condense** (`flow_condenser.py`). From each entry point, walk the resolved call graph and contract
every maximal chain containing no surviving dispatch site into a single `step` node. `DecisionProjector`
emits a `decision` node per surviving site and, for arms that terminate without reaching further
code, an `outcome` node named by `OutcomeLabeler` (`Returns` / `Raises` / `Continues`, or a
verdict-supplied label). `decision_seeder.py` attaches decisions whose owner is not call-reachable
from any entry. `StepMerger` collapses straight-line single-successor chains.

Node kinds: `entry | step | decision | parallel | effect | outcome`. `parallel` exists so that
`asyncio.gather`-style do-all fan-out never renders as a decision — an AND, not an XOR.

**Stitch** (`flow_stitcher.py`). `HttpStitchDetector` matches outbound URLs to route entries in other
lanes; `LlmStitchDetector` judges the residue.

**Budget** (`visibility_budgeter.py`). This is the second place the shipped system diverges from its
specification. The design called for a destructive one-page budget of ~35 nodes with **no
drill-down**. What shipped **deletes nothing** — it *demotes*:

- `BudgetRecondenser`, `ArmFolder`, `EffectCapper` collapse mergeable nodes via the shared
  `ContainerRepointer`, which re-parents contained nodes onto the survivor and refuses to introduce a
  containment cycle;
- `SequenceChainer` links same-owner body members with a `sequence` edge where safe;
- `ContainmentIndexer` computes each node's `level` (BFS depth over `containers`), `hidden_children`
  (topologically sorted immediate members — exactly what a `+` reveals), `body_kind`
  (`flow` | `list`), `body_head` and `body_tails`;
- `SkeletonReducer` **demotes** low-ranked nodes to a deeper `level` rather than removing them.

Ranking for demotion is by HITS hub/authority scores over the component graph
(`PillarRanker`, `hits_iteration.py`, 50 iterations, 6-decimal rounding for determinism), not by
call-graph reach — changed at `95f7033`, "Rank budget trimming by importance, not call-graph reach",
because reach over-weighted utility code.

Budget constants (`budget_config.py`): `skeleton_budget = 15`, `node_budget = 40`,
`max_reveal_per_node = 8`, `max_arms_per_decision = 5`, `max_body = 6`,
`seed_anchors_per_lane = 3`, `visible_decisions = 8`, `min_lane_nodes = 3`.

**Invariants** (`containment_invariants.py`): I1 (single-rooted DAG), I2 (total reachability from the
root) and I5 (cohesion) are hard asserts. I3 (single-entry flow bodies) is deliberately **a
derivation, not an assert** — asserting it crashed the pipeline on CodeFlow's own repository, because
a shared memoised node can legitimately be both a body member's predecessor and a containment
ancestor reached by a different path. `_assign_kind` classifies such a body `"list"` instead of
raising.

### 2.3.6 Worked example

Tracing one decision from raw source to rendered node. Target repository: `django-helpdesk`
(`LOCAL_REPO_PATH`), run at commit `b9779cf`.

**Stage 0 — raw source.** `helpdesk/views/staff.py`, lines 313–318:

```python
def ticket_perm_check(request, ticket):
    huser = HelpdeskUser(request.user)
    if not huser.can_access_queue(ticket.queue):     # line 315
        raise PermissionDenied()
    if not huser.can_access_ticket(ticket):          # line 317
        raise PermissionDenied()
```

**Stage 1–2 — index and resolve.** `ticket_perm_check` is indexed as
`src.helpdesk.views.staff.ticket_perm_check` with parameters `(request, ticket)`. `HelpdeskUser` is
resolved from the module's import bindings; `huser.can_access_ticket` resolves via rule (3) —
`huser` was assigned from an annotated construction — to
`src.helpdesk.user.HelpdeskUser.can_access_ticket`.

**Stage 3 — extract.** `BranchDetector` emits **two** `branch` sites, one per `if`:

```
DispatchSite(id="src.helpdesk.views.staff.ticket_perm_check:317",
             owner="src.helpdesk.views.staff.ticket_perm_check",
             kind="branch",
             selector_reads=("ticket",),      # the selector reads the `ticket` parameter
             arms=(Arm(index=0, terminal="raises", ...),   # the PermissionDenied path
                   Arm(index=1, terminal="falls_through", ...)),
             reconverges=False,
             span=SourceRef(file="src/helpdesk/views/staff.py", line=317, end_line=318))
```

**Stage 4 — score.** `ticket` **is** a parameter of the owner, and `ticket_perm_check` is
route-reachable (it is called from `delete_ticket`, `edit_ticket`, `view_ticket` and seven other
view functions), so `provenance = 2`. `reconverges = False`, so the terminal term fires. `kind =
branch`, so no kind bonus:

```
score = 3.0·log₂(1 + |live_union|) + 2.0·2 + 2.0·1 + 1.0·0
      = 3.0·log₂(1 + |live_union|) + 6.0
```

**Stage 5 — judge.** The candidate is sent with `kind="branch"`,
`enclosing_function="ticket_perm_check"`, its `arm_reach_sizes`, and the 25-line source snippet. The
LLM returns:

```json
{"id": "...:317", "verdict": "decision", "question": "User can access ticket?",
 "arm_labels": ["allowed", ...], "importance": <high>}
```

**This is the interesting part of the example.** The deterministic `SiteClassifier` would **not**
have returned `decision` here. One arm `raises` with a reach of ≤2 → classified `guard`; the other
falls through. That leaves one `live` arm plus a guard arm, which is exactly the
`return "guarded_step"` case. The heuristic would have demoted an **access-control decision** — the
kind of thing the prompt explicitly ranks highest — to a badge on a step. The LLM overrides it, and
the resulting node keeps a `"guarded"` badge as a trace of the disagreement.

This single site is the clearest available justification for `991bb11`, and it is also the source of
a **known, currently failing assertion**: `scripts/selfrun.py` checks "no guard-selector decision
survives" and reports **FAIL: 2 guard decisions**. The assertion encodes the original design;
the shipped behaviour deliberately contradicts it. One or the other should be retired — see §2.5.

**Stage 6–8 — condense, budget, render.** The node as it appears in `flow_graph.json`:

```json
{
  "id": "dec:src.helpdesk.views.staff.ticket_perm_check:317",
  "kind": "decision",
  "lane": "src",
  "label": "User can access ticket?",
  "llm_label": "User can access ticket?",
  "one_liner": "Checks if user has permission to access the specific ticket.",
  "refs": [{"file": "src/helpdesk/views/staff.py", "line": 317, "end_line": 318}],
  "badges": ["guarded"],
  "level": 3,
  "hidden_children": ["out:src.helpdesk.views.staff.ticket_perm_check:317:0"],
  "containers": ["dec:src.helpdesk.views.staff.ticket_perm_check:315"],
  "body_kind": "flow",
  "body_head": "out:src.helpdesk.views.staff.ticket_perm_check:317:0"
}
```

Its one `arm` edge carries `arm_label: "allowed"`; it has eleven outgoing `sequence` edges to the
view functions that call it, and one incoming `sequence` edge from
`dec:src.helpdesk.user.HelpdeskUser.has_full_access:58`.

Its containment chain, which is what a user walks by pressing `+`:

```
level 0  entry     root:django-helpdesk               "Django helpdesk"
level 1  decision  ...views.staff.attachment_del:2079 "Delete attachment requested?"
level 2  decision  ...views.staff.ticket_perm_check:315 "User can access queue?"
level 3  decision  ...views.staff.ticket_perm_check:317 "User can access ticket?"
```

**Note the defect this exposes.** The two permission checks nest correctly (315 contains 317, which
mirrors the source), but their parent is `"Delete attachment requested?"` — one arbitrary caller out
of eleven. `ticket_perm_check` is shared by eleven view functions; containment forced it under one.
The pipeline's own reviewer stage caught an instance of exactly this class of problem in the same
run: *"Parent node references AbstractTicketForm but decision is in lib.py queue_template_context
function, creating a structural mismatch."* This is discussed in §2.5.

---

## 2.4 Before/after comparison

**A same-input comparison is not possible from the repository, and it would be misleading to present
one.** The only preserved pre-pivot output (`b40216f:shared/outputs/tracer_output.json`) is for a
**web-scraper repository**, not `django-helpdesk`. No pre-pivot output for `django-helpdesk` exists
in any commit, and the pre-pivot pipeline was deleted in full at `774102a`.

What can be compared honestly is the **kind of artefact each produces**:

| | Before (`b40216f`, 14 Apr) | After (`b9779cf`, measured 8 Aug) |
|---|---|---|
| Input repository | web scraper | `django-helpdesk` (100 Python files) |
| Output type | `DiagramSpec` — layered component graph | `FlowGraph` — decision tree with containment |
| Total nodes | 20 components | **394** |
| Edges | 24 | **488** (`arm` 159, `sequence` 329) |
| Node kinds | components in 3 fixed layers | `decision` 222, `outcome` 105, `step` 34, `entry` 33 |
| Entry points | 1 | **33** |
| Decisions represented | **0** | **222** |
| Always-visible nodes | all 20 | 16 (skeleton budget 15) |
| Provenance | `file_path` per component | `file:line`+`end_line` per node; 469/508 nodes carry a `SourceRef` on the self-run |
| Determinism | not measured | **byte-identical across two runs** |

The structural difference is the point: the old artefact could not express a decision at all, so the
count is zero by construction rather than by measurement.

**A same-input comparison that would be valid** — and which a marker may reasonably want — is the
current pipeline run **with and without the LLM judge**, since `--no-llm` selects
`HeuristicDecisionJudge` on the identical static substrate:

```bash
python scripts/render_repo.py /path/to/django-helpdesk /tmp/llm
python scripts/render_repo.py --no-llm /path/to/django-helpdesk /tmp/heuristic
python scripts/flow_metrics.py /tmp/llm; python scripts/flow_metrics.py /tmp/heuristic
```

This is the one experiment in the project that isolates a single variable. `NOT YET RUN` — it is
recommended as the highest-value addition to the evaluation.

### Measured results, current pipeline

From `scripts/flow_metrics.py` on `django-helpdesk`, 8 August 2026 (exit code **0**):

```
nodes / edges     394 / 488
  edge kinds      {'arm': 159, 'sequence': 329}
kinds             {'decision': 222, 'entry': 33, 'step': 34, 'outcome': 105}
roots             1 ['root:django-helpdesk']
depth             {0: 1, 1: 61, 2: 109, 3: 133, 4: 48, 5: 29, 6: 11, 7: 1, 8: 1}
skeleton (lvl 0)  16  (budget 15)
bodies            198  (multi-member 106)
  body_kind       {'flow': 104, 'list': 94}
  decision forks  72  (23 fork only to outcomes)
  sequence bodies 34  (6 are chains)
I3 single-entry   15/16 flow bodies clean
I5 cohesion       0 violations
I2 unreachable    0
OVERLAPS          0
```

Two honest negatives in that output: the skeleton is **16 against a budget of 15**, and one flow body
fails the I3 single-entry property (informational, not a gate).

---

## 2.5 Design rationale and honest limitations

### Where the abstraction works well

**Framework-routed web applications.** The `route` detector turns a URLconf or a set of FastAPI
decorators into the richest and cheapest decision data available — 33 entries found in
`django-helpdesk` against the one the old pipeline reported.

**Permission and access control.** The worked example is representative: these are branches on
external input, in route-reachable functions, with materially different consequences. They score
maximum provenance (2) and the LLM prompt ranks them highest.

**Codebases following Open/Closed.** As argued in §2.3.0, decisions migrate into tables, routes and
polymorphic dispatch precisely in well-structured code, and the taxonomy catches all three.

### Where it breaks down

**1. Codebases with little branching — the abstraction has nothing to show.** Stated in `PROMPT.md`
as a known limit: *"Decisions expressed as classes are invisible. DDD `BusinessRule.is_broken()`
objects contain no fork, so fork detection sees nothing."* A domain model that replaces conditionals
with polymorphic rule objects — i.e. one following widely recommended practice — is invisible to the
detector unless the dispatch is through an annotated base type with ≥2 implementations.

**2. Declarative and configuration-driven systems.** *"Plugin/dynamic routing is invisible.
Supporting one project's service-locator idiom would mean hardcoding it."* The decision exists at
runtime, in configuration, and there is no fork in the source to detect. `DynamicDetector` records
the site honestly as unresolvable rather than guessing, which is the right call but produces a node
that says only "something is chosen here".

**3. Third-party SDK boundaries.** *"SDK-mediated HTTP is invisible. Effect detection matches
httpx/requests method names; a call made inside a third-party SDK produces no `EffectSite`."*

**4. Languages other than Python.** Stages 4–8 are language-agnostic given a per-language front end
(index + resolve + dispatch extraction), but the Python front end leans heavily on this codebase's
own disciplines — type annotations and constructor injection — for resolver rule (3), the workhorse.
An untyped Python codebase degrades to `dynamic`. `PROMPT.md`: *"Python-only analysis; JS/TS is not
traced."* No non-Python front end exists.

**5. Shared functions distort containment.** Demonstrated concretely in the worked example:
`ticket_perm_check` is called from eleven view functions, and containment forced it under one
arbitrarily. The containment model is a tree over a structure that is genuinely a DAG. The pipeline's
own reviewer flags instances of this, and `HANDOFF.md` §2 documents the related I3 concession. This
is a real limitation of the *presentation*, not the detection.

**6. The scoring weights have never been tuned.** `weight_reach=3.0`, `weight_provenance=2.0`,
`weight_terminal=2.0`, `weight_dispatch_kind=1.0` were introduced at `5874f20` (16 July) and are
unchanged. `git log -p -- significance_config.py` returns **two commits**, the second of which only
adds HITS parameters. There is no experiment in the repository justifying these values against any
alternative. Given the LLM judge now makes the survive/die call and the heuristic score only breaks
ties within the ranking, this matters less than it would have in the original design — but it should
be stated rather than implied to be empirical.

**7. The LLM now makes a structural decision, contradicting the project's own stated invariant.**
This is the most important self-criticism available. The governing principle is "static analysis owns
structure; the LLM judges significance and writes labels", and the LLM adds/removes no node. But
`991bb11` moved the *survive-or-die* verdict from `SiteClassifier` to the model. A fork the LLM calls
`noise` does not become a node. The invariant holds in the narrow sense (the model cannot invent a
node) but the set of nodes on the page is now model-determined, and **run-to-run stability rests on
temperature 0 plus the verdict cache rather than on the algorithm being deterministic.** The
determinism measurement in §2.4 is real, but it is determinism-with-a-warm-cache; a cache miss after
a `PROMPT_VERSION` bump re-queries the model.

**8. A shipped assertion now contradicts the shipped behaviour.** `selfrun.py`'s "no guard-selector
decision survives" fails with 2 guard decisions, and "lanes == {api, profiler, tracer, layout,
render}" fails because `explain` and `scripts` lanes now exist. 5 of 7 assertions pass. Both failures
are stale assertions rather than regressions — but `PROMPT.md` and `HANDOFF.md` both describe
`selfrun.py` as having **5** assertions, when it has 7. The documentation has drifted from the code.

**9. Top-level connectivity is thin.** Reading the rendered PNG (`scratch_out/flow.png`, per
`CLAUDE.md`'s "Always Run It And Look At The Picture"): the always-visible page shows a row of
eleven disconnected entry ovals, one three-node chain, and two isolated single nodes in separate
lanes. It is within budget and has zero overlaps, but as a *mental model* it is closer to a list of
entry points than to a connected picture of how the system decides. `HANDOFF.md` §6 lists this as a
known open defect. Node counts and invariant checks all pass on this diagram; **the counts are not
evidence that the picture is good**, which is exactly the failure mode `CLAUDE.md` warns about.

### Gaps and open questions

1. **The with-LLM / without-LLM comparison has not been run.** It is the single highest-value
   experiment available and requires one command (§2.4). It would quantify what the LLM judge
   contributes over the deterministic heuristic on identical static input.
2. **No ground truth exists for "is this fork a real decision?"** on any repository. Precision and
   recall of the judge are `NOT MEASURABLE FROM REPO`. Establishing it needs a hand-labelled sample
   of forks from `django-helpdesk` — feasible at, say, 100 sites, and would materially strengthen LO5.
3. **The 222 decisions on `django-helpdesk` have not been sampled for correctness.** The labels read
   plausibly, but plausibility is not accuracy. Reading the run log, at least three look like
   candidates the prompt should have excluded — *"Which encoding to use?"*, *"Which CSS class for
   priority?"*, *"Which logging level to apply?"* are formatting and logging branches, which the
   system prompt lists under NOT a decision.
4. **Cold-cache determinism is unverified.** The byte-identical result was obtained with a warm
   verdict cache. Deleting `.cache/decision_verdicts.json` between runs would test whether
   temperature 0 alone is sufficient.
5. **The design document's Stage 4 describes a divergence gate that the shipped system bypasses.**
   `SiteClassifier` still implements it and is still the offline default, but it no longer gates the
   production path. The relationship between the two judges should be stated in the dissertation
   rather than left implicit.
