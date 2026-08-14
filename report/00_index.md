# 00 — Evidence Pack Index

Verified, sourced facts about CodeFlow for the honours dissertation (due 14 August 2026). This is
evidence, not prose. Every claim is traceable to a commit SHA, file path, PBI or command output;
anything unmeasurable is marked `NOT MEASURABLE FROM REPO` with the command that would close it.

Compiled 8 August 2026 against commit `b9779cf` plus the uncommitted working tree.

---

## Contents

| Document | Covers | Learning outcomes |
|---|---|---|
| [`01_evolution.md`](01_evolution.md) | Chronology, seven design pivots, dead ends and reversals | LO1, LO4 |
| [`02_decision_algorithm.md`](02_decision_algorithm.md) | **The core contribution.** What it replaced, the failure mode, the algorithm in reimplementable detail, a worked example, honest limitations | LO3, LO4, LO5 |
| [`03_system.md`](03_system.md) | Architecture as built, tech stack, data contracts, frontend, codebase metrics, compliance self-audit | LO3, LO6 |
| [`04_objectives_audit.md`](04_objectives_audit.md) | Status, evidence and commentary per interim-report objective | LO4 |
| [`05_evaluation_inputs.md`](05_evaluation_inputs.md) | Evaluation artefacts, ethics materials, reproducibility, determinism, accuracy numbers | LO5 |
| [`06_appendices.md`](06_appendices.md) | Full schemas, configuration, prompts verbatim, work-package record | LO6 |

---

## What a marker should read first

**Read `02_decision_algorithm.md` §2.2 and §2.3.** §2.2 shows, from a recovered April 2026 output,
that the old pipeline produced a twenty-component diagram in which the word "decision" does not
appear once — `MatchingEngine` is described as using "multiple matching strategies" while which
strategy runs, and on what basis, is unrepresentable. §2.3 is the replacement, specified precisely
enough to reimplement, with a worked example tracing one Django permission check from source through
detection, scoring, LLM judgement and into the rendered node.

Then read **§2.5**, which is where the project is most critical of itself.

---

## The five things this pack establishes

**1. The central pivot is real, dated and documented in advance.** The decision algorithm replaced
call-graph tracing across thirteen specified features (F01–F13, `features/`) implemented in thirteen
consecutive commits on 15–16 July 2026, ending in a cut-over that deleted **5,473 lines** (`774102a`).
The design rationale was written before the code (`docs/decision_flow_tracer.md`, `f986fa0`).

**2. Determinism holds, with one qualification.** Two consecutive runs on `django-helpdesk` produce a
byte-identical `flow_graph.json`; `flow_metrics.py` exits 0 with zero unreachable nodes, zero
cohesion violations and zero overlapping boxes. The qualification: both runs used a warm verdict
cache, so cold-cache determinism is untested. One command would settle it
(`05_evaluation_inputs.md` §5.4).

**3. Three of seven objectives were delivered; two were superseded and two never started.** That
summary understates the outcome, because the work that displaced objectives 2 and 6 is the project's
main contribution — but objectives 4 and 5 need straight answers, and `04_objectives_audit.md` gives
them.

**4. Engineering discipline is unusually well evidenced.** One file in the entire backend exceeds the
project's own 150-line limit (`api/dependencies.py`, 266 lines, the composition root). Constructor
injection throughout, no global state, 1,395 lines of purpose-built test harness, and a rule set in
`CLAUDE.md` written in direct response to named incidents.

**5. There is no automated accuracy measurement.** The evaluation harness was deleted on 15 July 2026
and never replaced. The core algorithm then changed completely with quality judged by reading a PNG.
This is the pack's most significant negative finding and it is stated as such throughout.

---

## Three things to act on before submission

Ordered by urgency.

**1. The evaluation study has not started.** The ethics application (28 July, approved design: an
anonymous Microsoft Forms questionnaire, 8–12 developers, ~30 minutes) gives a project window of
4–14 August 2026 — ending on the dissertation deadline. The questionnaire instrument does not exist,
and the participant information sheet is still the **unfilled university template**
(`[INSERT CONTEXT]`, `[INSERT METHOD(S) AND CONTEXT]`, `[INSERT YOUR NAME & CONTACT]`). This is the
largest single risk to the LO5 mark. See `04_objectives_audit.md` §7.

**2. Run the with-LLM / without-LLM comparison.** One command, one variable isolated, on a repository
that is not CodeFlow:

```bash
python scripts/render_repo.py --no-llm /path/to/django-helpdesk /tmp/heuristic
python scripts/flow_metrics.py /tmp/heuristic     # compare against the LLM run
```

It is the highest-value experiment available and the cheapest. If the questionnaire cannot be run in
time, this is the fallback with the best evidence-to-effort ratio.

**3. Commit the working tree, and fill the empty files.** `FlowchartView.jsx` and seven helpers are
untracked; if the dissertation cites the frame's flowchart view, commit it first. Separately,
`README.md` is 10 bytes and `docker-compose.yml` is 0 bytes — both are among the first files a
marker opens, and there is no `.env.example`, so a marker cannot configure a clone without reading
`api/core/config.py`.

---

## Corrections to the brief this pack was written from

Six points where the repository contradicted the description of it:

1. **Aetos is not the test case.** It appears nowhere in the repository — no code, commit or
   artefact. The standing target is `django-helpdesk` (`.env: LOCAL_REPO_PATH`), and `CLAUDE.md`
   requires validation on a repository that is not CodeFlow.
2. **JARVIS was retired.** The brief presents `pyan3 → jarviscg` as the endpoint of call-graph
   tooling. `jarviscg` was removed entirely at `774102a` because it "cannot supply call-site
   context". This is a seventh pivot, documented as (g) in `01_evolution.md`.
3. **The evidence/critic–actor loop is deleted**, not current — removed with the rest of the legacy
   pipeline at `774102a`.
4. **The validation rules are R1–R6, not R1–R7.** W1–W5 is correct. The split is three-way, not
   two-way: R1–R6 auto-fix, W1/W2/W5 are re-prompted, W3/W4 are reported only. The three-attempt cap
   is confirmed. All recovered from git and documented in `02_decision_algorithm.md` §2.1.
5. **The LLM now makes a structural decision.** Since `991bb11` (29 July) the survive-or-die verdict
   sits with the model, not with the deterministic `SiteClassifier`. The stated invariant ("the LLM
   may never add, remove, merge or rewire") holds in the letter but the set of nodes on the page is
   model-determined. Presenting the pipeline as purely deterministic would overclaim.
6. **The design document is partly superseded by what shipped.** `docs/decision_flow_tracer.md`
   specifies one page, no drill-down, budget ~35. The delivered system uses progressive disclosure
   with a 15-node skeleton and deletes nothing. The document was never updated.

---

## Method

`git log`/`show`/`diff` across all branches and 131 commits (85 on `main`); `git log -S<symbol>` to
date every named component's introduction and removal; `git show <sha>:<path>` to recover deleted
files and superseded outputs. Live measurements from `render_repo.py` (twice, for the determinism
diff), `flow_metrics.py`, `selfrun.py` and `screenshot_flow.py`, run on `django-helpdesk` on
8 August 2026. The rendered PNG was read directly, per `CLAUDE.md`'s "Always Run It And Look At The
Picture" — which is why `03_system.md` and `04_objectives_audit.md` report thin top-level
connectivity that every numeric check passes.

No source code was modified. Everything written by this task lives in `report/`.
