# PBI 60 — Linear runs render as a pipeline; siblings stop overlapping

Two independent defects, both visible in user screenshots of a depth-2/3 reveal on
django-helpdesk. Stages 1–3 (PBIs 57–59) are complete and accepted; do not redesign them.

**Frontend changes ARE authorized for this PBI** — but only the files named in §3 and §4.
Nothing else under `frontend/`.

---

## 1. Defect A — sibling subtrees overlap horizontally

`HiddenEmitter._block` (`agents/render_agent/placement/hidden_emitter.py`) allocates every child a
fixed slot of `col_step` (= widest node 220 + `column_gutter` 120 = 340px), 3 per row, centred on
the parent. Those offsets are baked in the backend, which **cannot know which nodes the user has
expanded**.

`placeChildren` (`frontend/src/hooks/useExpansion.js`) then calls `pushBelow` to shift later nodes
**down** when a block is inserted — but there is no horizontal equivalent. When a revealed child is
itself expanded, its subtree grows sideways past its 340px slot and lands on top of its sibling and
its sibling's group box.

Observed: a decision's orange body box overlapping the neighbouring green body box, and child nodes
straddling box borders.

**This is why the fix must live on the frontend**: sibling spacing depends on what is currently
expanded, which is frontend state.

## 2. Defect B — single-path decisions shrink and look like decisions

`shape_for(node, arm_count)` in `agents/render_agent/placement/flow_node_treatment.py` accepts
`arm_count` and **never reads it** — every `kind == "decision"` node gets the `decision` shape.
`scaleOf(depth)` (`frontend/src/components/flow/depthScale.js`, `0.76 ** depth`, floor `0.42`) then
shrinks each nested level, so a straight chain of one-path decisions marches down the canvas getting
progressively smaller.

A decision with one outgoing path is not a decision — there is no alternative branch. It reads as a
**command**: a thing that gets done. A run of them should read as a **pipeline / bullet list** —
uniform size, stacked, aligned — not a shrinking staircase.

---

## 3. Backend changes

`agents/render_agent/placement/flow_node_treatment.py`
- `shape_for`: when `node.kind == "decision"` and `arm_count <= 1`, return `"rect"`.
  Real forks (`arm_count >= 2`) keep `"decision"`. `arm_counts` is already threaded through
  `HiddenEmitter.payloads` and `flow_emit` — no new plumbing.
- `node_data`: add `"linear": True` when the same condition holds, so the frontend can identify a
  linear run without recomputing arm counts.

**Do not change the graph.** Static analysis owns structure (CLAUDE.md). This is a *treatment*
concern only: no node is added, removed, merged or rewired, and `node.kind` stays `"decision"`.
`flow_graph.json` must be byte-identical to before this PBI — only `rendered_view.json` changes.

`agents/render_agent/placement/flow_grid_config.py`
- Only if needed after §4 lands. Prefer fixing spacing in the frontend where expansion state lives.

## 4. Frontend changes (authorized, these files only)

`frontend/src/hooks/useExpansion.js`
- **Linear runs.** In `placeChildren`, when `pending.length === 1` and that child is `linear`, do
  **not** apply `scaleOf(depth)` — reuse the parent's scale. Place it directly below the parent at a
  fixed row gap and **left-align it with the parent** (`x` = parent `x`), rather than centring it.
  Consecutive such nodes then form a uniform-width vertical pipeline. Depth scale continues to apply
  normally at real forks (`pending.length >= 2`) and to non-linear children.
- **Sibling spacing.** Replace the fixed-slot placement with measured widths: lay out children
  bottom-up so each sibling is allocated a horizontal slot equal to the actual extent of its own
  rendered subtree (its nested box rect, not just its own node width), plus a gutter. Shift later
  siblings right by any overflow — the horizontal analogue of the existing `pushBelow`.
- Keep the existing `MAX_BOX_DEPTH` box behaviour unchanged.

`frontend/src/hooks/expansionBoxes.js`
- `rectOf` already unions nested rects; make sure the measured extent used for §4 spacing is the
  same rect the box draws, so box and spacing can never disagree.

`frontend/src/components/flow/depthScale.js`
- Only if a helper is needed for the linear-run case. Do not change `DEPTH_SCALE` or `MIN_SCALE`
  globally — that would shrink or grow every existing diagram.

## 5. Out of scope

- Do **not** relabel decisions to imperative wording. The labels still read as questions
  ("Is queue email address defined?") where a command would read better, but that is an LLM prompt
  change requiring a `PROMPT_VERSION` bump and full cache invalidation. Logged separately.
- Do not add invariants I4 or I7.
- Do not touch the top-level skeleton layout or `PillarGatewaySelector`.

## 6. Acceptance

- `python scripts/render_repo.py /Users/cooperkeenan/github/django-helpdesk /tmp/hd` exits 0;
  `python scripts/flow_metrics.py /tmp/hd` exits 0 with **roots 1, I5 0, I2 0, OVERLAPS 0**.
- Same for CodeFlow (`. /tmp/cf`).
- `flow_graph.json` byte-identical to pre-PBI for both repos (this PBI must not alter the graph).
- `python scripts/selfrun.py` → 4/5, same single deliberate red, no crash.
- **`flow_agent.py` DOM overlap check is 0 at depth 3**, which is where the reported collision
  appears. This is the acceptance test for Defect A and the previous stage's known bug:
  ```
  python scripts/flow_agent.py /Users/cooperkeenan/github/django-helpdesk --rebuild state overlaps
  ```
  then expand a decision, expand one of its children, and re-check `overlaps` — must be **0**.
- Every file touched <= 150 lines.

## 7. Look at the picture — this PBI is judged on the image, not the counts

Reproduce the two reported views and compare against the screenshots that prompted this PBI:

```
python scripts/screenshot_flow.py --save cooperkeenan /Users/cooperkeenan/github/django-helpdesk
python scripts/flow_agent.py /Users/cooperkeenan/github/django-helpdesk --rebuild \
  "toggle:entry:seed:src.helpdesk.models.Queue" fit "shot:scratch_out/p60_a.png"
```
Then expand a nested decision two levels deep and shoot `scratch_out/p60_b.png`.

Open both with the Read tool and answer directly:
1. Do any group boxes or nodes overlap? (must be no)
2. Does a run of single-path nodes read as a uniform pipeline / bullet list, or as a shrinking
   staircase? (must be the former)

Counts are not evidence. If it still looks wrong, say so with the image description rather than
reporting the green numbers.
