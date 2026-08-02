# Handoff — Progressive-disclosure decision diagram

Read this first. It states the next job, what already works, and every known gap.

Branch: `featue/decision-nodes`. Open PR: #14. **5 commits are local and unpushed.**

---

## 1. The job

The diagram currently renders everything it has chosen to show, all at once, in one flat page.
The user wants **progressive disclosure**:

- **One high-level diagram of the whole codebase**, always visible. This is the skeleton — the
  services, entry points and major outcomes. It must stay readable at a glance.
- **A `+` / `−` control per branch** that reveals or hides the decisions sitting *between* a parent
  and its outcomes. Expanding one branch must not disturb the rest of the page.
- The high-level view is never navigated away from. There is no drill-down to a separate page —
  detail is spliced into the diagram in place.

The user's reference sketch:

```
                 Orchestrator
                /            \
        (Correct Product ID?)  (Correct Product ID?)
              |                       |
        Regulatory Agent           MRF Agent
              |                       |
     (Do we need both services?)   (CPM Data?)
        /        \                    |
     CPT Tool   MUE Tool          Query MRF Data
```

Grey = outcomes (services, agents, tools, handlers). Orange = decisions. **The orange nodes are
what `+` reveals.** Note their position: a decision sits *on the edge* between a parent and its
outcome. Collapsed, `Orchestrator → Regulatory Agent`; expanded, `Orchestrator → (Correct Product
ID?) → Regulatory Agent`.

That shape matters for the data model. A decision is best treated as an **edge annotation that
gets promoted to a node on expand**, not as a node that is hidden and shown. Modelling it as a
hidden node forces the layout to reflow the whole page on every toggle.

### Design constraint that is currently violated

The backend today **destroys** decisions to fit a page budget (`BudgetConfig.node_budget = 40`,
`visible_decisions = 8`). For progressive disclosure the backend must instead **emit the full tree
with a visibility level per node**, and let the frontend decide what to draw. Folding must become
reversible metadata, not deletion. This is the single biggest change required.

---

## 2. What already works — do not rebuild it

| Stage | Where | State |
|---|---|---|
| Import resolution | `services/analysis/path_fqn.py` | ancestor-prefix, layout-agnostic |
| Service roots | `service_root_resolver.py` + `project_indexer.py` | derived from imports |
| Fork extraction | `dispatch_extractor.py` + `*_detector.py` | branch/match/except/route/table/polymorphic/dynamic |
| **Decision judging** | `llm_decision_judge.py`, `prompts/decision_judge_prompt.py` | LLM decides real decision vs guard, writes the question |
| Verdict cache | `verdict_cache.py`, `decision_fingerprint.py` | content-addressed, prompt-versioned |
| Entry points | `fastapi_route_scanner.py`, `django_route_scanner.py` | FastAPI + Django URLconf |
| Tree geometry | `placement/tree_layout.py`, `tree_structure.py` | tidy tree, parent centring, cycle-safe |
| Screenshot loop | `scripts/screenshot_flow.py` | renders any local repo to a PNG |
| Account save | `scripts/repo_map_saver.py` | `--save <handle>` writes a viewable `repo_maps` row |

**The demo/test repo is `django-helpdesk`**, cloned at `/Users/cooperkeenan/github/django-helpdesk`
and set as `LOCAL_REPO_PATH`. It is a support-ticket system: relatable for a demo, conventional
Django routing, and decision-dense. Its decisions read like *"User can access ticket?"*, *"Create
new ticket or update only?"*, *"User has queue access?"*, *"User is superuser?"*.

---

## 3. Gap analysis

### 3a. Blocking the main job

**G1 — Most decisions never reach the graph.** On django-helpdesk the judge finds **225** decisions;
**43** nodes reach the graph; **8** decisions render. Ranking cannot promote what was never
condensed in. `DecisionSeeder` attaches decisions whose owner is unreachable from an entry to a flat
synthetic anchor (`entry:seed:<root>`), which both loses hierarchy and caps how many arrive. Until
this is fixed, progressive disclosure has almost nothing to disclose.

**G2 — The graph is a forest, not a tree.** `tree_layout.py` is correct; it is handed a graph with
many roots and faithfully draws many disconnected islands. Measure before changing anything:

```python
from placement.tree_structure import build_forest, select_root
from placement.flow_reach import longest_path_depths
```
Print root count, per-root subtree size and child count, and max depth. TA_Platform was 17 roots /
depth 3; django-oscar 3 roots / depth 5. **A tree is 1 root.**

**G3 — No expand/collapse anywhere.** `FlowNode.folded_count` is emitted and `NodeChrome.jsx`
renders it as a `chip`, but nothing consumes a click. `useGraphTransform.js` maps view nodes 1:1
with no expansion state. `FlowPage.jsx`'s only interaction is a provenance popover. This is the
user-facing half of the job and it is entirely unbuilt.

**G4 — Decisions are modelled as ordinary nodes.** To splice a decision onto an edge on expand,
either the edge must carry its hidden decision, or the node must carry enough parent/child context
to be inserted without a full relayout. Decide this deliberately before writing frontend code.

### 3b. Detection limits (known and documented — not bugs to "fix" blindly)

**G5 — SDK-mediated HTTP is invisible.** `effect_registry.py` detects outbound HTTP by matching
httpx/requests/aiohttp method names. A call made *inside* a third-party SDK (e.g.
`agent_framework.a2a`) produces no `EffectSite`, so no cross-service candidate exists.
`LlmStitchDetector` is built, cached and working — it correctly returns "no match" on genuine
third-party calls — but on TA_Platform it has nothing to judge. Widening effect detection to
recognise a client constructed with a URL argument would create the candidate.

**G6 — Decisions expressed as classes are invisible.** DDD-style codebases encode rules as objects:
`class SellerMustBeEligible(BusinessRule): def is_broken(self) -> bool: return ...`. There is no
fork, so fork detection sees nothing. This is a real limitation of the technique and worth stating
plainly in the dissertation rather than papering over.

**G7 — Plugin/dynamic routing is invisible.** django-oscar wires views through
`OscarConfig.get_urls()` and a string-keyed `get_class()` service locator. Supporting it would mean
hardcoding one project's idioms — correctly rejected.

### 3c. Engineering debt

**G8 — Lint and types.** `ruff check .` fails with ~200 errors; **193 of these pre-date this work**
(mostly `B008` function-call-in-default-argument and unsorted imports on `main`). Roughly 8 were
added recently. `mypy` reports 6 errors, 2 of them ours in `llm_decision_judge.py:69,91` (indexing
`dict[str, Any]` with `Any | None`). CI runs both and has been red on `main` for a while.

**G9 — CD is not gated on CI.** `.github/workflows/cd.yml` triggers on push to `main`, builds five
backend images and runs `railway redeploy`. Its `deploy` job only `needs: push-images`, so a red
lint never blocks a deploy. **The frontend is not in the pipeline at all** — it is served via the
Cloudflare tunnel (`tunnel.sh`).

**G10 — Unpushed work.** Five commits sit on `featue/decision-nodes`. The user asked about deploying
the branch directly via `scripts/build-push.sh` rather than through the `main` pipeline; that was
never done and is still open.

**G11 — Ranking is only half-effective.** `DecisionAdmitter._score` now orders by
`(importance, score)`, but with only 8 of 225 decisions present the ordering rarely bites. Re-check
once G1 is fixed.

**G12 — Host disk.** The dev machine ran out of space mid-session. `ENOSPC` kills `Bash` entirely,
since it cannot write its own output file. Keep temp files small and clean up after yourself.

---

## 4. How to run and verify

```bash
cd /Users/cooperkeenan/GitHub/CodeFlow && source venv/bin/activate

python scripts/render_repo.py /Users/cooperkeenan/github/django-helpdesk /tmp/hd   # JSON + decision list
python scripts/render_repo.py /Users/cooperkeenan/github/django-helpdesk /tmp/hd2  # run twice
diff /tmp/hd/flow_graph.json /tmp/hd2/flow_graph.json                              # must be empty

python scripts/selfrun.py                                                          # 5 assertions, must pass
python scripts/screenshot_flow.py /Users/cooperkeenan/github/django-helpdesk       # PNG of the real page
python scripts/screenshot_flow.py --save cooperkeenan <repo>                       # also save to the account
```

`scratch_out/flow.png` can be opened with the Read tool. **Look at it every iteration** — in this
project the metrics improved several times while the picture got worse. `--no-llm` forces the
deterministic heuristic judge. The verdict cache is at `.cache/decision_verdicts.json`; deleting it
costs a cold re-judge (~4 min on django-helpdesk, ~12 min on django-oscar).

For frontend work, `/flow-fixture` renders the real `FlowPage` against
`frontend/public/fixture/rendered_view.json` with no API, DB or login.

---

## 5. Constraints

- `CLAUDE.md` is law: ≤150 lines per file, one class per file, constructor injection, type
  annotations, no docstrings or explanatory comments, no unsolicited tests.
- **Determinism**: same repo in → byte-identical `flow_graph.json` out. Sort every set/dict
  iteration; break ties on `(file, line, name)`. The LLM runs at temperature 0 behind a
  content-addressed cache; bump `PROMPT_VERSION` when a prompt changes, or stale verdicts get reused.
- **Static analysis owns structure.** The LLM judges significance and writes labels. It may never
  add, remove, merge or rewire a node or edge.
- **No domain hardcoding.** Framework support (FastAPI, Django) is fine. Searching for "agent",
  "tool", or one project's idioms is not.
- **Validate on a repo that is not CodeFlow.** Two separate bugs here were invisible because
  CodeFlow satisfies its own assumptions by construction — see `CLAUDE.md`.
- Never weaken an assertion to make a run pass. If one genuinely no longer applies, say so and leave
  it failing.
