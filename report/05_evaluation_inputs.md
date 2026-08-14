# 05 — Evaluation Material

What exists to evaluate the system with, what it measures, and what it does not.

**The headline finding, stated first because it shapes everything below: the project has no automated
accuracy measurement.** The evaluation harness was deleted on 15 July 2026 and never replaced. What
exists instead is a structural-invariant harness, which is a genuine and unusual engineering
contribution but measures *well-formedness*, not *correctness*.

---

## 5.1 Evaluation artefacts in the repository

### What is there

| Artefact | Location | What it does |
|---|---|---|
| `flow_metrics.py` | `scripts/` | Structural invariant harness — exit 0 or non-zero |
| `selfrun.py` | `scripts/` | In-process self-analysis, 7 assertions |
| `flow_agent.py` | `scripts/` | Drives the real page in headless Chrome; reports state as assertable text |
| `screenshot_flow.py` | `scripts/` | Renders any local repo to PNG, no API/DB/login |
| `render_repo.py` | `scripts/` | Runs the pipeline to JSON; `--no-llm` forces the deterministic judge |
| `flow_probe_js.py`, `flow_reports.py`, `flow_session.py`, `dev_server*.py` | `scripts/` | Harness support |
| `dump_explain.py` | `scripts/` | Builds real explain payloads for frame testing |
| Verdict caches | `.cache/*.json` | 5,655 judged forks — see §5.4 |

`scripts/` is 1,395 lines across 17 files. This is substantial and deliberate engineering, motivated
by an explicit methodological rule in `CLAUDE.md`:

> "Counts are not evidence. Overlapping nodes, spaghetti edges, empty canvases and 50-node fans all
> pass every assertion in this repo. Metrics here have improved several times while the diagram got
> visibly worse."

### What is not there

- **No evaluation harness.** `evaluation/` contains only untracked, stale `__pycache__`;
  `git ls-files evaluation` returns nothing. Deleted at `f986fa0` (15 July 2026): *"Delete
  evaluation/ (stale, covered only module/edge recall)"*. The replacement proposed in the same
  commit's design document — *"a handful of fixture repos with committed expected FlowGraphs — a
  plain snapshot test"* (`docs/decision_flow_tracer.md` §6) — **was never built.**
- **No unit tests.** `CLAUDE.md` forbids unsolicited tests; there is no `tests/` directory and no
  test runner configured.
- **No interview scripts, questionnaire instrument, participant materials or results** in the
  repository. Ethics artefacts exist outside it — see §5.2.
- **No output samples designated as evaluation stimuli.** `scratch_out/` holds ~60 development
  screenshots, not a curated set.

### The consequence

The core algorithm changed completely between 15 July and 4 August 2026 — the period covering the
decision-algorithm pivot, the LLM judge, HITS-based ranking and progressive disclosure — **with no
automated accuracy measurement in place at any point.** Every quality judgement in that window came
from reading a PNG. That is a real and stateable process weakness (LO4), somewhat mitigated by the
fact that "read the PNG" was made a formal, documented step rather than an ad-hoc habit.

---

## 5.2 Ethics and participant materials

These live **outside** the repository, in `~/Documents/Uni/Year_4/TR2/Honours_Project/` and
`~/Downloads/`.

| Artefact | Status |
|---|---|
| `Ethics_Form_CodeFlow_COMPLETED.docx` (28 Jul 2026, 1,879 words) | **Complete**, bar two placeholders: `[Napier student email — TO CONFIRM]`, `[Contact number — TO CONFIRM]` |
| `Information sheet and consent form.docx` | **Unfilled university template** — `[INSERT CONTEXT]`, `[INSERT METHOD(S) AND CONTEXT]`, `[INSERT YOUR NAME & CONTACT]` |
| Questionnaire instrument | **Does not exist** |
| Participant responses | **Do not exist** |
| Ethics approval confirmation | **Not found** |

The approved design (from the ethics form) is a single anonymous Microsoft Forms questionnaire,
8–12 adult software developers and computing students, ~30 minutes, online. Participants nominate a
repository they wrote or know well, run it through the CodeFlow web tool, and grade the output:

> "are the entry points correct, are the decision points shown genuine, has anything significant been
> missed, and does anything shown not actually exist in the code"

That is a precision/recall framing evaluated against ground truth the participant already holds — a
well-designed instrument for this system, and the right answer to the missing-accuracy-measurement
problem. Analysis is planned as *"counts of correct, missing and incorrect diagram elements, median
Likert ratings, and thematic grouping of free-text comments."*

**The study has not been run.** Project window per the form: 4 August – 14 August 2026, the second
date being the dissertation deadline. See `04_objectives_audit.md` §7 for the risk assessment.

---

## 5.3 Reproducibility

### What a marker needs

Software: Python 3.10+, Node 18+, Google Chrome (the Playwright harness uses the installed browser
via `channel="chrome"`, so no browser download). An Anthropic API key. A Neon Postgres URL **only**
for the web application — not for the analysis pipeline.

### End-to-end from a fresh clone

```bash
git clone <repo> && cd CodeFlow
python3.10 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt          # Playwright, for the interaction harness

cp .env.example .env                          # DOES NOT EXIST — see gaps
# .env must define: ANTHROPIC_API_KEY, LOCAL_REPO_PATH, DATABASE_URL,
#                   ENVIRONMENT=local, GitHub OAuth credentials

# --- the pipeline alone: no API, no database, no login ---
python scripts/render_repo.py /path/to/target-repo /tmp/out
python scripts/flow_metrics.py /tmp/out                    # must exit 0
python scripts/screenshot_flow.py /path/to/target-repo     # → scratch_out/flow.png

# --- determinism check ---
python scripts/render_repo.py /path/to/target-repo /tmp/a
python scripts/render_repo.py /path/to/target-repo /tmp/b
diff /tmp/a/flow_graph.json /tmp/b/flow_graph.json         # must be empty

# --- the deterministic judge, no API key needed ---
python scripts/render_repo.py --no-llm /path/to/target-repo /tmp/heuristic

# --- interaction ---
python scripts/flow_agent.py <repo> --rebuild state overlaps      # overlaps must be 0
python scripts/flow_agent.py <repo> "toggle:<node_id>" fit "shot:out.png"

# --- self-analysis ---
python scripts/selfrun.py

# --- the full web application ---
# VS Code task "CodeFlow: All Services" starts six uvicorn apps (8000, 8002-8004, 8006-8007)
cd frontend && npm install && npm run dev
```

**`render_repo.py` is the reproducibility story that matters.** It runs the entire analysis pipeline
against any local directory with no gateway, no database and no authentication. A marker can verify
the project's central claim — deterministic decision extraction — with one command and an API key.
`--no-llm` removes even the API key requirement, at the cost of substituting the heuristic judge.

**Cost and time.** Cold run on `django-helpdesk` (100 Python files) ≈ 4 minutes; warm ≈ 3 seconds.
The difference is the verdict cache. Model: `claude-haiku-4-5-20251001`, batched 20 candidates per
call, temperature 0.

### Validation target

`CLAUDE.md` requires validation on a repository that is **not** CodeFlow:

> "CodeFlow satisfies its own assumptions by construction, so a self-run hides exactly the bugs that
> matter."

The standing target is `django-helpdesk` (`LOCAL_REPO_PATH`). This rule was written in response to
two real outages — `path_fqn.agent_root_of` and `service_root_resolver.root_of` both hardcoded
CodeFlow's own directory layout, and both were invisible under self-testing.

---

## 5.4 Determinism assessment

Measured 8 August 2026 on `django-helpdesk` at commit `b9779cf`.

```
$ python scripts/render_repo.py <repo> /tmp/hd1      # exit 0
$ python scripts/render_repo.py <repo> /tmp/hd2      # exit 0
$ diff /tmp/hd1/flow_graph.json /tmp/hd2/flow_graph.json
DETERMINISM: IDENTICAL
```

`selfrun.py` independently confirms it on CodeFlow itself: **[PASS] two runs byte-identical
(ignoring `llm_*`)**.

### Stage-by-stage

| Stage | Deterministic? | Why |
|---|---|---|
| 1 Index (`project_indexer`) | **Yes** | Pure function of file contents; imports resolve by ancestor-prefix walk |
| 2 Resolve (`call_resolver`) | **Yes** | Pure function of the index |
| 3 Extract forks (`dispatch_extractor`) | **Yes** | Seven detectors run in fixed order |
| 4 Effects, reach, score | **Yes** | Sorted iteration throughout; HITS rounded to 6 decimals (`pillar_score_decimals`) specifically to prevent float drift |
| **5 Judge** | **No — cached** | Model call. Stable via temperature 0 + content-addressed cache keyed on source, arm labels, reach sizes and `PROMPT_VERSION` |
| 6 Condense, 7 Stitch (URL) | **Yes** | Graph construction over sorted inputs |
| 7 Stitch (residual) | **No — cached** | `LlmStitchDetector`, same caching scheme |
| Labelling (`FlowNamer`) | **No — cached** | Writes only `llm_label` / `one_liner`; `selfrun` explicitly ignores `llm_*` when comparing |
| Review (`FlowReviewer`) | **No — cached** | Advisory findings only; asserted not to change node/edge counts |
| 8 Budget, layout | **Yes** | `FlowGraph` sorts itself canonically on validation |

### The honest qualification

**The measured determinism is determinism-with-a-warm-cache.** Both runs read
`.cache/decision_verdicts.json`, so stage 5 made no model calls in the second run and few in the
first. The claim that survives without qualification is narrower and still worth making:

> Given the same verdicts, the pipeline is byte-for-byte reproducible; and verdicts are stable
> because they are content-addressed and cached, so a given fork is judged once ever.

What is **not** demonstrated is that a cold run — cache deleted — reproduces the same verdicts from
the model. Temperature 0 makes it likely; nothing in the repository measures it. This is a one-command
gap:

```bash
mv .cache/decision_verdicts.json /tmp/ && python scripts/render_repo.py <repo> /tmp/cold
diff /tmp/hd1/flow_graph.json /tmp/cold/flow_graph.json
```

Running that would let the dissertation state the determinism claim without a caveat, or state
honestly where it breaks. **It is recommended.**

A second qualification: `PROMPT_VERSION` (currently `"2"` in `decision_judge_prompt.py`) is part of
the cache key and must be bumped when the prompt changes, or stale verdicts are silently reused
(`CLAUDE.md` §Determinism). This is a manual step with no automated guard.

---

## 5.5 Accuracy tracking already recorded

There are **no scorecards across runs and no per-run diffs** in the repository — the harness that
would have produced them was deleted. What exists is three sources of raw numbers, pulled together
here for the first time.

### (a) Judge verdict distribution — 5,655 forks

From `.cache/decision_verdicts.json`, accumulated across every repository analysed to date:

| Verdict | Count | Share |
|---|---|---|
| `guarded_step` | 3,556 | 62.9% |
| `decision` | 1,561 | 27.6% |
| `noise` | 538 | 9.5% |
| **Total** | **5,655** | |

This is the closest thing the project has to a behavioural measure of the LLM judge: it discards or
demotes **72.4%** of candidate forks. That the majority land in `guarded_step` rather than `noise` is
consistent with the prompt's design — most branches in real code are guards and validation, which the
prompt explicitly excludes from being decisions.

**This is a distribution, not an accuracy measure.** Nothing here says whether the 1,561 were the
*right* 1,561.

### (b) Structural harness, `django-helpdesk`, 8 Aug 2026 — `flow_metrics.py`, exit 0

| Metric | Value | Gate? |
|---|---|---|
| Nodes / edges | 394 / 488 | no |
| Edge kinds | `arm` 159, `sequence` 329 | no |
| Node kinds | `decision` 222, `outcome` 105, `step` 34, `entry` 33 | no |
| Roots | 1 (`root:django-helpdesk`) | **yes (I1)** |
| Unreachable nodes (I2) | **0** | **yes** |
| Cohesion violations (I5) | **0** | **yes** |
| Overlapping node boxes | **0** | **yes** |
| Skeleton (level 0) | **16, budget 15** | no — *overshoot* |
| I3 single-entry flow bodies | 15/16 | no (derivation, not assert) |
| Containment depth | levels 0–8 | no |
| Decision forks / sequence bodies | 72 / 34 | no |

Two honest negatives: the skeleton exceeds its own budget by one, and one flow body fails I3.

### (c) Self-analysis — `selfrun.py`, 8 Aug 2026

508 nodes, 708 edges, 4 stitches, 181 decisions, 16 skeleton nodes. **5 of 7 assertions pass.**

| Assertion | Result |
|---|---|
| ≥4 stitch edges api→agent entries | **PASS** (4) |
| Two runs byte-identical (ignoring `llm_*`) | **PASS** |
| Skeleton within budget ceiling | **PASS** (16 of 508) |
| Every revealed node reachable from a parent's `hidden_children` | **PASS** (0 stranded) |
| Node/edge counts unchanged across reviewer stage | **PASS** (508n/708e both sides) |
| `lanes == {api, profiler, tracer, layout, render}` | **FAIL** — `explain` and `scripts` lanes now exist |
| No guard-selector decision survives | **FAIL** — 2 guard decisions |

Provenance: **469 of 508 nodes carry a `SourceRef`**; the 39 without are entries, which lack refs by
construction.

Both failures are **stale assertions rather than regressions.** The first predates the explain agent.
The second encodes the original deterministic design, which `991bb11` deliberately overrode — see
`02_decision_algorithm.md` §2.3.6, where the worked example *is* one of those two guard decisions and
is an access-control check the heuristic would have wrongly demoted.

Per `CLAUDE.md` §"Do Not Weaken Checks To Go Green", these are left failing and reported rather than
adjusted. Note also a documentation drift: `PROMPT.md` and `HANDOFF.md` both describe `selfrun.py`
as having **5** assertions; it has 7.

---

## Gaps and open questions

1. **No accuracy measurement of any kind exists.** Precision and recall of decision detection are
   `NOT MEASURABLE FROM REPO`. The planned questionnaire is the intended remedy and has not been run.
   A cheaper interim measure: hand-label ~100 forks from `django-helpdesk` and score the judge
   against them.
2. **The with-LLM / without-LLM comparison has not been run.** One command
   (`render_repo.py --no-llm`), one variable isolated, on a non-CodeFlow repository. This is the
   highest-value experiment available and it is cheap. **Strongly recommended.**
3. **Cold-cache determinism is unverified.** §5.4 gives the two-line command.
4. **No `.env.example` exists**, so the reproduction instructions above name the required variables
   from `api/core/config.py` and `PROMPT.md` rather than from a template. A marker cloning the
   repository cannot configure it without reading the source. Creating one is trivial and worth doing.
5. **`README.md` is 10 bytes and `docker-compose.yml` is empty.** Both are the first files a marker
   opens.
6. **The 222 decisions on `django-helpdesk` have not been sampled for correctness.** Reading the run
   log, at least three appear to contradict the judge's own prompt, which excludes formatting and
   logging branches: *"Which encoding to use?"*, *"Which CSS class for priority?"*, *"Which logging
   level to apply?"*. A 20-item manual sample would give the dissertation a defensible error rate for
   very little effort.
7. **No results exist from any repository other than `django-helpdesk` and CodeFlow itself.** The
   questionnaire design (participants nominate their own repositories) would fix this, and is the
   main reason it is worth running.
8. **Verdict-cache figures are cumulative and unattributed.** The 5,655 entries span every repository
   analysed during development; they cannot be broken down per repository, and they include verdicts
   made under `PROMPT_VERSION` 1 as well as 2.
