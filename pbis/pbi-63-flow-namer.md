# PBI 63 — `FlowNamer`: cached, batched LLM naming inside the tracer

Every node in the diagram is currently labelled by the deterministic fallback. The LLM naming
stage exists but has **never run in the verification loop**. This PBI moves naming into the tracer
so it runs in every path.

**Frontend changes are NOT authorized in this PBI.** Backend only.

PBIs 57–62 are complete and accepted; do not redesign them.

---

## 1. The evidence — read this before writing anything

From the current `scratch_out/flow_graph.json` (CodeFlow self-run, 418 nodes, 16 at level 0):

```
[decision] 'Which data source?'      llm=None  one_liner=''
[entry   ] 'Branch Detector'         llm=None  one_liner=''
[entry   ] 'Django Route Scanner'    llm=None  one_liner=''
[step    ] 'Is Linear'               llm=None  one_liner=''
[effect  ] 'Respond'                 llm=None  one_liner=''
[effect  ] 'Respond'                 llm=None  one_liner=''
page_title = ''
```

Every node has `llm_label = None` and `one_liner = ""`. The reason:

- `scripts/screenshot_flow.py:31-42`, `scripts/render_repo.py:91-92` and `scripts/selfrun.py:62-65`
  all go `pipeline.run()` → `build_flow_page_placer().place()`.
- The **only** writer of `llm_label` / `one_liner` is
  `agents/layout_agent/services/planning/flow_labeler.py:64-65`, and the layout agent is invoked
  **only** from the gateway (`api/services/analysis_service.py:87-91`).
- So the loop CLAUDE.md mandates has never displayed an LLM-written label. `Is Linear`,
  `Branch Detector` and `Django Route Scanner` are humanised function/class names — precisely what
  `agents/layout_agent/prompts/flow_label_prompt.py:16` forbids.

Two further defects in the existing labeller that this PBI must not reproduce:

- **It cannot scale.** `flow_labeler.py:34-40` makes **one** call with `max_tokens=4000` for the
  entire graph. At 418 nodes the response truncates, the `re.search(r"\{.*\}")` at `:42` fails, and
  `:28-30` silently returns the graph unchanged. Batch, like `LlmDecisionJudge` does.
- **It is uncached and non-deterministic.** Every run is re-billed. `scripts/selfrun.py:111-120`
  has to strip `llm_*` before asserting byte-identical reruns because of this.

Separately, fix a pre-existing bug found on the way: `agents/tracer_agent/dependencies.py:40-46`
constructs `FlowPipeline` **without** `judge=`, so `significance_filter_factory.py:24` resolves to
`HeuristicDecisionJudge` and the served `/trace` endpoint never uses the LLM decision judge
regardless of API key.

## 2. What you may write

`llm_label` and `one_liner` only. **Do not write `label`.**

This is safe and provable: no structural code path reads any label. `containment_indexer.py` keys
off `containers` and the edge set; `skeleton_reducer.py:113-122` ranks on
gateway/pillar/kind/out-degree/backing/id; `shared/models/flow_graph.py:70-78` sorts edges on
`arm_label` but not `llm_label`. `node.label` is the deterministic static-analysis output and
`scripts/selfrun.py:70` regex-asserts against it — leave it alone.

CLAUDE.md is law here: **"The LLM must never add, remove, merge or rewire a node or edge."** This
stage renames. It does nothing else.

## 3. New files — `agents/tracer_agent/`

Follow the existing one-class-per-file, constructor-injection, ≤150-line conventions.

| File | Contents |
|---|---|
| `models/node_naming.py` | frozen dataclass `NodeNaming{label: str, one_liner: str}` |
| `services/analysis/flow_naming.py` | `FlowNaming` Protocol, one method `name(graph: FlowGraph) -> FlowGraph`. Copy the 8-line shape of `services/analysis/decision_judge.py:7-8` |
| `prompts/flow_name_prompt.py` | `PROMPT_VERSION = "1"`, system prompt, per-node evidence builder |
| `services/analysis/name_fingerprint.py` | sha256 content-address. Copy `decision_fingerprint.py:9-17` in shape |
| `services/analysis/name_cache.py` | copy `services/analysis/verdict_cache.py` (54 lines) with a `NodeNaming` payload |
| `services/analysis/name_validator.py` | id-drop + word caps. Mirrors `agents/layout_agent/helpers/flow_label_validator.py` |
| `services/analysis/heuristic_flow_namer.py` | returns the graph unchanged — the no-key / `--no-llm` fallback |
| `services/analysis/flow_namer.py` | the LLM implementation |
| `services/analysis/flow_namer_factory.py` | env branch. Copy `decision_judge_factory.py:12-18` |

### 3a. The prompt (`prompts/flow_name_prompt.py`)

Port the naming-style rules from `agents/layout_agent/prompts/flow_label_prompt.py:10-17` — they
are good rules and the user wants them kept — with two changes:

- Raise the node label cap from 6 words to **10 words**. The user's words: *"some nodes should have
  longer names so the user can understand the flow better."* A 10-word label must still be a phrase,
  not a sentence.
- A `one_liner` is now **required for every node**, not optional. It is about to be displayed on the
  node face (PBI 65), so an empty one leaves a visible gap.

Keep the existing per-kind style rules verbatim: steps are verb phrases, decisions are the question
being decided, arms are the answer, effects are a noun for the side effect and its target,
entries are a short verb phrase. Keep **"Never a class, function, or file name unless nothing better
exists"** — that rule is exactly what today's output violates.

Send per node: `id`, `kind`, `deterministic_label`, `backing`, `refs[0]` as `file:line`,
`effect_kind` / `effect_target`, arm `label_source`s for decisions, and the deterministic labels of
its `hidden_children` (so the model can name a parent in terms of what it contains).

### 3b. The fingerprint (`services/analysis/name_fingerprint.py`)

```
sha256("\x1f".join([
    PROMPT_VERSION, node.kind, node.label,
    *sorted(node.backing),
    *arm_label_sources, effect_kind or "", effect_target or "",
    *sorted(child_deterministic_labels),
]))
```

Deliberately **exclude `node.id` and absolute paths**, so the key is content-addressed and
repo-location independent — two structurally identical nodes are named once. This mirrors
`decision_fingerprint.py`, which excludes file/line/owner for the same reason.

CLAUDE.md: bump `PROMPT_VERSION` whenever the prompt text changes, or stale cached names are
silently reused.

### 3c. The namer (`services/analysis/flow_namer.py`)

Copy the control flow of `llm_decision_judge.py:30-88` — it is the reference implementation and it
already solves batching, deduplication and per-batch degradation:

1. Fingerprint every node.
2. Cache hits resolve immediately.
3. Dedupe misses by fingerprint into groups; send **one representative per group**.
4. Chunk representatives 20 per call.
5. Fan each result back to every duplicate in its group.
6. `cache.flush()` once at the end.

Use the **sync** `anthropic.Anthropic` client — `FlowPipeline.run` is sync (`flow_pipeline.py:52`).
`_MODEL = "claude-haiku-4-5-20251001"`, `temperature=0`, `max_tokens=4000`. Per-batch
`try/except Exception` → log a warning and fall back for that batch only, exactly as
`llm_decision_judge.py:56-73`. Backfill any id the model omitted.

### 3d. The validator (`services/analysis/name_validator.py`)

Build the id set from the graph and **drop any id the model invented** — this is the structural
guard that makes "the LLM cannot rewire the graph" true by construction rather than by trust. Copy
the drop-unknown-id pattern at `flow_label_validator.py:32,48,60`. Cap label to 10 words, one_liner
to 120 chars.

## 4. Modified files

- **`services/analysis/flow_pipeline.py`** (74 lines) — accept `namer: FlowNaming | None = None`
  alongside the existing `judge`. Apply it to the budgeter's output at `:74` before returning.
  Naming is the last thing that happens.
- **`agents/tracer_agent/dependencies.py:40-46`** — pass **both** `judge=build_decision_judge(...)`
  and `namer=build_flow_namer(...)`. This also fixes the served-path judge bug in §1.
- **`scripts/render_repo.py:85`**, **`scripts/screenshot_flow.py:34`**, **`scripts/selfrun.py:57`**
  — thread `--no-llm` through the namer using the same one-line ternary already used for the judge.
- **`scripts/selfrun.py:111-120`** — add `node.one_liner = ""` to `_canonical`. This is **not**
  weakening a check: the function's stated job is stripping LLM-authored display fields and it
  already strips `llm_label` on the adjacent line. The real determinism guarantee is the
  content-addressed cache; the strip only covers a cold first run.

**Cache path:** `REPO_ROOT/.cache/node_names.json`, alongside `decision_verdicts.json`.

## 5. Out of scope

- No frontend changes. The node face still shows only the label — PBI 65 handles display.
- No sibling-aware review, no duplicate disambiguation, no `page_title`, no lane titles — PBI 64.
- Do not delete or modify `agents/layout_agent/` — PBI 64 handles the retirement.
- Do not touch structure, containment, the budgeter or the skeleton.

## 6. Acceptance

- Every node in `flow_graph.json` has a non-empty `llm_label` **and** a non-empty `one_liner`, on
  both django-helpdesk and CodeFlow.
- Labels no longer read as bare function names. `Is Linear` and `Branch Detector` must be gone.
- Two consecutive `render_repo.py` runs → `diff` on `flow_graph.json` is **empty**.
- `python scripts/flow_metrics.py /tmp/hd` exits **0**, with the same numbers as before this PBI —
  it reads no labels, so nothing structural may move.
- `python scripts/selfrun.py` → 4/5, same single deliberate red, no crash.
- Warm run stays ≈3s. Report the cold-run wall time and the number of LLM calls.
- **Cold-cache run must be verified**: `mv .cache/node_names.json /tmp/` and re-run on
  django-helpdesk. This exercises the batching path on a 400+ node graph — the exact failure mode
  that silently broke the existing labeller. A truncated response that falls back to unnamed nodes
  is a **fail**, not a pass.
- Every file touched ≤ 150 lines.

## 7. Look at the picture

```
python scripts/screenshot_flow.py --save cooperkeenan /Users/cooperkeenan/github/django-helpdesk
python scripts/flow_agent.py /Users/cooperkeenan/github/django-helpdesk --rebuild state
```

`flow_agent.py state` prints every visible node's label as text — it is the one harness that
surfaces naming as assertable output. Open `scratch_out/flow.png` with the Read tool and answer:

1. Does every visible node read as a **human description of what happens**, or still as a
   humanised identifier?
2. Are any two visible nodes labelled identically? (Expect some — PBI 64 fixes that. Record which.)
3. Did anything move on the canvas? Nothing should have — this PBI changes strings only.

Report honest negatives with real numbers. Do not present a partial result as success.
