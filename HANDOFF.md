# Handoff — Decision-Flow Tracer: the diagram shows the wrong thing

Read this first. It explains what was built, what's wrong, and the exact next step.
Branch: `claude/codeflow-decision-diagrams-ea5bn1`. Open PR: **#14** (`cooperkeenan/CodeFlow`).

---

## 1. Mission (what the user actually asked for)

> "An algorithm that traverses the codebase, finds the **key decision nodes**, and lays the
> whole codebase out as a human would map it in their head."

The mental model is a **decision tree**, not a wiring/flow diagram. The canonical example
(from `docs/decision_flow_tracer.md` and the user's own sketch):

```
                 Orchestrator
                /            \
        (Correct Product ID?)   (Correct Product ID?)
              |                       |
        Regulatory Agent           MRF Agent
              |                       |
     (Do we need both services?)   (CPM Data?)
        /        \                    |
     CPT Tool   MUE Tool          Query MRF Data
```

- **Decisions are the load-bearing structure.** Gray nodes = outcomes (agents, tools);
  orange nodes = decisions ("which agent?", "do we need both services?").
- **Top-down tree**, rooted at the main orchestrator/entry.
- A **"+" depth control** reveals the next, finer layer of decisions in place (progressive
  reveal on one page — NOT navigate-away drill-down). The orange nodes in the sketch are
  what "+" reveals.
- Infrastructure (health checks, CRUD, auth, plumbing) is **secondary** — hidden by default,
  "added later."

## 2. What was actually built (F01–F13, all on the branch, PR #14)

A full static-analysis pipeline. **The engine that finds decisions EXISTS and works** — the
problem is the output is organized around the wrong axis. Stages (all under
`agents/tracer_agent/services/analysis/` unless noted):

| stage | file | status |
|---|---|---|
| F01 FlowGraph contract | `shared/models/flow_graph.py` | ✅ solid |
| F02 index | `project_indexer.py` (+ factory) | ✅ |
| F03 call resolver (call graph + control context) | `call_resolver.py` | ✅ |
| F04 **dispatch extraction (finds crossroads)** | `dispatch_extractor.py` + `*_detector.py` | ✅ **this is the decision-finder** |
| F05 effects (http/db/llm/response) | `effect_detector.py` (+ factory) | ✅ |
| F06 **significance filter (decision vs guard)** | `significance_filter.py`, `site_classifier.py`, `reach_computer.py` | ✅ **this ranks decisions** |
| F07 condensation → FlowGraph | `flow_condenser.py` | ⚠️ entry-first (see §3) |
| F08 cross-service stitching | `flow_stitcher.py` | ✅ |
| F09 one-page budget | `page_budgeter.py` | ❌ **folds decisions, protects entries — backwards** |
| F10 LLM labeling (only LLM stage) | `agents/layout_agent/services/planning/flow_labeler.py` | ✅ |
| F11 layout geometry | `agents/render_agent/placement/flow_page_placer.py` | ⚠️ left-right swimlanes, not a tree |
| F12 frontend one page | `frontend/src/pages/FlowPage.jsx` | ✅ renders whatever backend emits |
| F13 cutover + delete legacy | wired across all 4 agents | ✅ |

The pipeline runs end-to-end, is **byte-identical across runs**, every node carries a
`file:line` ref. Self-run: `python scripts/selfrun.py` (runs the whole thing in-process on
CodeFlow). Spec for every stage: `features/01`–`13`.

## 3. The core problem — WHY the output is wrong

The user ran it on `TA_Platform` (an LLM-agent orchestration system with real routing
decisions) and got a **flat vertical list of ~18 API routes all flowing into "Check service
health" → "Respond"** — i.e. an *inventory of entry points*, with **zero decision nodes**.
The decision tree — the entire point — did not appear.

Two compounding mistakes, both in the OUTPUT, not the engine:

1. **Entry-first, not decision-first.** `flow_condenser.py` makes every route an entry node
   and lays them out left→right in swimlanes (`FlowPagePlacer`). It never picks a **root**
   and branches from its **decisions**. There is no tree.
2. **The budget is inverted.** `page_budgeter.py` **protects entries and folds decisions**.
   On CodeFlow, **0 decisions survive** the budget; pre-budget there are only ~3 (CodeFlow is
   a near-linear pipeline). So the presentation throws away exactly the nodes that matter.

A third, honest trap: the pipeline was **only ever validated on CodeFlow itself**, which is
nearly decision-free — so "0 decisions, here are the routes" looked *plausible* and the
absence of the whole point went unnoticed. **Do not repeat this — validate on a
decision-heavy repo.**

## 4. THE IMMEDIATE NEXT STEP (do this before any rework)

We must answer one question first, because the fix differs:
**On TA_Platform, are the orchestrator's decisions FOUND-BUT-FOLDED, or NOT-DETECTED?**

Agent routing is frequently an **LLM tool-call** or an **agent registry/dict**, which F04 can
only partially see (it flags `dynamic` dispatch but can't name the branches). So:

1. Ask the user to add the repo: `cooperkeenan/TA_Platform` (use `add_repo`, then clone +
   `register_repo_root`). The user offered this.
2. Run **only** F02→F06 on it in-process (recipe in §6) and **dump the raw decision list**:
   every `DispatchSite` with its `SiteVerdict` (decision/guard/noise), kind, owner, and
   arm reach sizes — BEFORE condensation/budget/layout.
3. Interpret:
   - If the "CPT vs MRF agent" crossroad **is** in the list as a `decision` → it's a
     **presentation problem** (§5a): re-center layout + budget on decisions. Medium effort.
   - If it's **absent or classified `dynamic`/`noise`** → it's a **detection problem** (§5b):
     the orchestrator routes via a registry/LLM the static detectors miss. Deeper work.

Paste that decision list to the user. Stop guessing from screenshots.

## 5. The reframe (what "good" requires)

### 5a. Presentation fixes (needed regardless)
- **Decision-first tree.** Root = the primary orchestrator entry (the one whose subtree
  contains the most/highest-scored decisions). Build the tree from decisions; outcomes
  (agents/tools/effects) hang below. Rework `flow_condenser.py` to emit a decision-rooted
  tree and `FlowPagePlacer` to lay it out **top-down** (like the sketch), not left-right lanes.
- **Invert the budget.** `page_budgeter.py` must **rank and keep decisions first**, and demote
  routes/health/CRUD/plumbing (fold or hide them). Today it does the opposite.
- **Bring back the "+" depth control.** The original design (`docs/decision_flow_tracer.md`,
  "depth control") had it; it was dropped for a static one-page budget. The user wants top
  decisions shown, "+" reveals the next layer **in place**. `FlowNode.folded_count` + the
  frontend's existing progressive-reveal mechanism are the hooks. This partially revisits the
  earlier "one page, no drill-down" decision — reconcile as: one page that starts shallow and
  expands decisions on demand, not separate drill pages.
- **Relevance ranking.** Business-logic decisions rank above infrastructure. Health/CRUD/auth
  routes should not dominate. (Route-entry grouping by router already exists in
  `entry_finder.py::_grouped` — a start, but entries still shouldn't be the skeleton.)

### 5b. Detection fixes (only if §4 shows decisions are missed)
- Teach F04/F05 to recognize **agent-registry dispatch** (a dict/list of agent or tool
  objects the orchestrator selects from) and **LLM tool-routing** (tool definitions passed to
  an LLM call = the branch set; each tool = an arm). This is the hybrid the original design
  doc anticipated: static analysis gathers candidate crossroads, the LLM names them. For agent
  systems the "arms" may come from tool/agent registries and system prompts, not `if` bodies.
- `dynamic` dispatch should not be silently dropped — a runtime-routed fan-out to N known
  agents IS the decision; surface it (honestly labeled) rather than folding it.

## 6. How to run / verify (verified-working recipe)

Self-run (in-process, on CodeFlow): `python scripts/selfrun.py` — asserts lanes, stitches,
byte-identical, budget ceiling, provenance.

Full pipeline wiring (sys.path = repo root + `agents/tracer_agent`; add `agents/render_agent`
too for layout, and put tracer FIRST so `services.analysis` resolves):

```python
idx = build_project_indexer().index(files)                 # files: dict[relpath, source]
cs  = CallResolver(idx).resolve_project()
disp = build_dispatch_extractor(idx).extract(cs)           # <-- DispatchSites (the crossroads)
eff = EffectDetector(CallEffectMatcher(EffectTargetExtractor()),
                     RouteHandlerInspector(), StoreEffectSurfacer()).detect(idx, cs)
sig = build_significance_filter(idx, SignificanceConfig()).run(cs, disp)  # <-- verdicts + ranking
graph = build_flow_condenser().condense("Repo", idx, cs, disp, eff, sig)
entries = EntryFinder(idx, RouteHandlerLocator(idx), ServiceRootResolver(None),
                      LabelSynthesizer()).find(disp)
stitched = build_flow_stitcher().stitch(graph, eff, entries)
budgeted = build_page_budgeter().budget(stitched, sig)     # <-- FlowGraph (shared.models.flow_graph)
```

Factories are `*_factory.py` next to each service. For §4, stop after `sig` and print
`disp` + `sig.verdicts` + `sig.ranked_decisions`.

To inspect geometry, run `FlowPagePlacer` (`build_flow_page_placer().place(graph)`) and look
at node `position` x/y. (A layout blowup on cyclic graphs was already fixed in
`flow_reach.py` — Kahn topological longest-path; the FlowGraph is NOT a guaranteed DAG.)

## 7. Constraints (do not violate)

- `CLAUDE.md` is law: ≤150 lines/file, constructor injection, one class per file, type
  annotations everywhere, no explanatory comments/docstrings, no unused imports, no unsolicited
  tests (the self-run script is solicited).
- **Determinism is non-negotiable:** same repo in → byte-identical FlowGraph out (labels
  excepted; the one LLM call is temperature 0). Sort all set/dict iteration; ties break on
  `(file, line, name)`.
- **Static analysis owns structure; the LLM only names things.** The labeler may never add,
  remove, merge, or rewire a node/edge.
- Workflow the user uses: Opus plans + reviews, spawns a **Sonnet sub-agent per feature**,
  reviews the diff against that feature's acceptance before committing. Each sub-agent starts
  cold — point it at the specific `features/*.md` + the files it touches.

## 8. Git / ops

- Commit as `Claude <noreply@anthropic.com>`; end messages with the Co-Authored-By +
  Claude-Session trailers already used on the branch.
- Push `-u origin claude/codeflow-decision-diagrams-ea5bn1` with exponential-backoff retry.
- Don't open a new PR — #14 is the one. Don't push to other branches.
- GitHub ops via `mcp__github__*` (load with ToolSearch). No `gh` CLI.

## 9. What was done THIS session (already committed/pushed)

- Built F01–F13, cut over all 4 agents to the FlowGraph pipeline, deleted the legacy
  chunk-tracing/assembly/layout stack + jarviscg. Self-run green.
- Fixed a catastrophic layout blowup (cycle → x=18,460) — `flow_reach.py` cycle-safe.
- Added route-entry grouping by router (`entry_finder.py::_grouped`) — api entries 24→7.
  Helpful but does NOT fix the core problem: the diagram is still entry-first, not a
  decision tree.

**The next agent's job is §4 then §5 — make the decision tree the primary output.** Start by
adding TA_Platform and dumping the raw decision list. Don't rebuild the engine; re-point it.
