# PBI 64 — `FlowReviewer`: sibling-aware coherence pass, and retire duplicate labelling

PBI 63 names each node from its own local evidence. That cannot catch problems that are only
visible when you look at several nodes **together**. This PBI adds the second pass, and retires the
now-duplicate labelling in the layout agent.

**Do not start until PBI 63 is accepted.** This PBI reads the names it produces.

**Frontend changes are NOT authorized in this PBI.** Backend + gateway only.

---

## 1. What pass 1 cannot see

From the current self-run, two separate effect nodes both render as `Respond`:

```
[effect] 'Respond'   refs: agents/tracer_agent/routers/...
[effect] 'Respond'   refs: agents/layout_agent/routers/...
```

Each is individually a correct name. They are only *wrong together* — on the canvas the user sees
two identical boxes and cannot tell them apart. Pass 1 fingerprints on content and deliberately
excludes `node.id`, so it will name both identically **by design**.

Also unfixable per-node: `page_title` is `""` (the diagram is titled *"flow"* in the header), lane
titles are unset, and sibling labels are not phrased in parallel.

## 2. The pass

One LLM call over a bundle of every level-0 node plus each one's immediate `hidden_children` —
roughly 60 items on django-helpdesk, comfortably inside `max_tokens`. Each item carries its pass-1
`llm_label` and `one_liner`, its `kind`, `lane` and `file:line`.

Ask the model for:

- **Corrected labels** where two siblings are indistinguishable, or a label is still a bare
  function/class name, or a set of siblings would read better phrased in parallel.
- **A `page_title`** for the whole diagram.
- **Lane titles**.
- **A `findings` array** of `{node_id, issue}` for problems it cannot fix by renaming.

Because the bundle is small and stable, cache it whole — one fingerprint over the serialised bundle.

## 3. Findings are reported, never applied

This is the constraint that matters. CLAUDE.md:122-125: **"The LLM must never add, remove, merge or
rewire a node or edge."**

The reviewer will notice things it cannot fix — a decision with zero arms, a node whose one_liner
contradicts its `file:line`, an entry that reaches nothing. Those go into a findings list that is
printed and stored. **The pipeline does not act on them.** No node is dropped, demoted, merged or
re-parented as a result of a finding. If the reviewer's output would change any node or edge count,
that is a bug in this PBI.

The value of a finding is that it tells a human where to look next. That is enough.

## 4. New files — `agents/tracer_agent/`

| File | Contents |
|---|---|
| `prompts/flow_review_prompt.py` | `PROMPT_VERSION = "1"`, system prompt, bundle builder |
| `models/review_finding.py` | frozen dataclass `ReviewFinding{node_id: str, issue: str}` |
| `services/analysis/flow_reviewer.py` | one call over the bundle; reuses PBI 63's `name_validator.py` for id-drop and word caps |
| `services/analysis/review_fingerprint.py` | sha256 over `PROMPT_VERSION` + the serialised bundle |
| `services/analysis/review_cache.py` | same shape as PBI 63's `name_cache.py` |
| `services/analysis/flow_reviewer_factory.py` | same env branch as `flow_namer_factory.py` |

Reuse `name_validator.py` rather than writing a second validator — the id-drop guard is the same
guard. Same 10-word label cap, same 120-char one_liner cap. Findings whose `node_id` is not in the
graph are dropped like any other invented id.

## 5. Modified files

- **`services/analysis/flow_pipeline.py`** — run the reviewer immediately after the namer. Expose
  findings through a `last_review()` accessor, following the existing `last_significance()` /
  `last_pillars()` pattern at `:46,49`.
- **`scripts/render_repo.py`** — print findings after `_print_significance` (`:63-70` is the
  template to copy).
- Write findings into `graph.meta["review_findings"]`, alongside the `meta["skeleton_nodes"]` etc.
  already written at `visibility_budgeter.py:94-99`.

## 6. Retire the layout agent's labelling

`FlowLabeler` is now a second writer of the same fields and would **overwrite** the tracer's names
in the gateway path. Disconnect it — but do not delete the service.

- **`api/services/analysis_service.py:87-91` and `:52-55`** — drop the layout call. Keep writing
  `layout.json` (now the tracer's output verbatim) so the existing
  `POST /analyse/local/from-layout` replay route at `api/routers/analysis.py:96-112` keeps working.
  Verify that route still round-trips.
- **`api/services/progress_tracker.py:1`** — remove `"layout"` from `_STAGES`. The percent maths at
  `:33` is derived and adapts. Check `api/services/stage_status_service.py:8,13` for the same list.
- **Leave `agents/layout_agent/` itself in place and unreferenced**, exactly as `HANDOFF.md` §5
  treats the editable-diagram slice. Deleting the service, its CD image in
  `.github/workflows/cd.yml` and its gateway client is a separate follow-up — not this PBI.

## 7. Out of scope

- No frontend changes.
- Do not let findings influence structure in any way (see §3).
- Do not add an invariant or an assert that fails on a finding — findings are advisory. A count
  threshold that fails the build was considered and explicitly rejected by the user.
- Do not delete `agents/layout_agent/`.

## 8. Acceptance

- The two `Respond` nodes get **distinct** names. Quote both, before and after.
- `page_title` is non-empty, and the page header no longer reads *"flow"*.
- Lane titles are populated.
- Findings print with real node ids that exist in the graph. Quote the full list — an empty list on
  a 418-node graph is a suspicious result, not a clean one; say so if that is what you get.
- **Node and edge counts are byte-identical across the reviewer stage.** Assert this in
  `scripts/selfrun.py` — count nodes and edges before and after, and fail if they differ. This is
  the check that enforces §3.
- Two consecutive `render_repo.py` runs → `diff` on `flow_graph.json` is **empty**.
- `python scripts/flow_metrics.py /tmp/hd` exits **0** with the same numbers as before this PBI.
- `python scripts/selfrun.py` → 4/5 plus the new assertion passing, no crash.
- The gateway path still completes end to end with layout removed from the stage list, and the
  progress bar reaches 100%.
- Every file touched ≤ 150 lines.

## 9. Look at the picture

```
python scripts/screenshot_flow.py --save cooperkeenan /Users/cooperkeenan/github/django-helpdesk
python scripts/flow_agent.py /Users/cooperkeenan/github/django-helpdesk --rebuild state
```

Open `scratch_out/flow.png` with the Read tool and answer:

1. Is the page title now a real description of the repo?
2. Are any two visible nodes still labelled identically?
3. Do sibling nodes read as a coherent set — same voice, same level of detail — or as a jumble?
4. Did anything move on the canvas? Nothing should have.

Then read the findings list and say plainly whether the problems it names are real. If the reviewer
is inventing complaints or missing the obvious ones, that is the result to report — do not tune the
prompt until the list merely looks tidy.
