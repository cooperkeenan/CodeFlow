# PBI 65 — The full card: label + summary + provenance on every node face

The user's ask: *"it would be good if we could put more information in each rectangle so it doesn't
have to keep drilling down."*

**Frontend changes ARE authorized** — but only the files named in §3.

**Do not start until PBI 63 is accepted.** This PBI displays the `one_liner` that PBI 63 populates;
without it every card renders with an empty second line.

---

## 1. The evidence

Node boxes are 220×60 holding a single 11px line (`shared/models/node_geometry.py:10-19`,
`frontend/src/components/flow/styles.js:19-32`) — roughly **80% empty** — on a canvas that is about
**85% unused**. Open `scratch_out/flow.png` and you can see both facts at once.

Meanwhile the information the user wants is **already being shipped to the frontend** and is only
reachable by clicking:

- `agents/render_agent/placement/flow_node_treatment.py:60-63` puts `oneLiner`, `backing` and
  `refs` into every node's data payload.
- `frontend/src/components/flow/NodeChrome.jsx:16,29` already has a `subtitle` slot. **Only
  `EffectNode.jsx:26` passes it.** The other six node components ignore it, so `data.oneLiner` is
  never rendered on a face.
- `ProvenancePopover.jsx` is the only surface that shows `oneLiner`, `backing` or `refs` — and it is
  click-driven. That is the drilling the user wants to stop doing.

So this is mostly a wiring and sizing job, not new plumbing.

## 2. Backend

- **`shared/models/node_geometry.py:10-19`** — enlarge to fit the card. Proposed starting point;
  adjust if the rendered card overflows:

  | shape | from | to |
  |---|---|---|
  | `pill` (entry) | 220×60 | 280×110 |
  | `rect` (step) | 180×60 | 280×110 |
  | `decision` | 200×68 | 280×118 |
  | `effect` | 184×60 | 280×110 |
  | `pipeline` | 200×44 | 280×92 |
  | `split_bar` | 200×40 | 240×56 |
  | `outcome` | 160×52 | 200×72 |
  | `lane_header` | 220×44 | unchanged |

  This single edit propagates correctly: `flow_grid_config.py:19-24` derives `col_step` and
  `row_step` from `max(NODE_GEOMETRY)`, so spacing widens automatically (340→400 and 100→150) and
  the `scripts/flow_metrics.py:54-70` overlap gate stays consistent by construction. Do **not**
  hand-tune `column_gutter` / `row_gutter` to compensate.

- **`agents/render_agent/placement/flow_node_treatment.py:53-64`** — add a `provenance` key to the
  data payload: `f"{basename(refs[0].file)}:{refs[0].line}"` when `refs` is non-empty, omitted
  otherwise. Use the basename, not the full path — a full path will not fit and the popover already
  shows it in full.

## 3. Frontend — the card

Target layout, top to bottom, inside one box:

```
┌────────────────────────────────┐
│ Scan Django URLconf for        │   label, up to 3 lines
│ route entries             [+1] │   folded-count chip, right
│ Walks urlpatterns, include()   │   one_liner, up to 2 lines
│ and CBVs via MRO to find views │
│ ────────────────────────────── │   hairline
│ django_route_scanner.py:31  ⟳  │   provenance + badges
└────────────────────────────────┘
```

- **`components/flow/NodeChrome.jsx`** — render `data.oneLiner` as the subtitle when no explicit
  `subtitle` prop is passed, so all seven node kinds get it and `EffectNode`'s
  `subtitle={data.effectTarget}` still wins where it is more specific. Add a provenance footer line
  below the badges. Raise `SUBTITLE_STYLE.WebkitLineClamp` from 1 to 2 and change
  `wordBreak: 'break-all'` to `'break-word'` (`:9,12`) — `break-all` mid-word hyphenates file paths
  and reads badly.
- **`components/flow/styles.js:28`** — `LABEL_STYLE.WebkitLineClamp` 2 → 3, to carry PBI 63's
  10-word labels. Add a `PROVENANCE_STYLE`: 8px, `TEXT_MUTED`, `nowrap` + ellipsis, hairline top
  border.
- **`components/flow/nodes/*.jsx`** — all seven components hard-code a duplicate `FALLBACK`
  geometry constant at line 5, each a copy of a `NODE_GEOMETRY` row. They are already a drift
  hazard and this PBI changes every value. Replace all seven with one shared
  `components/flow/geometryFallback.js`. Also update `hooks/expansionBoxes.js:5`
  `FALLBACK_GEOMETRY` and the `?? 200` / `?? 60` defaults at
  `components/flow/CameraController.jsx:11-12`.
- **`components/flow/depthScale.js:2`** — raise `MIN_SCALE` from `0.42` to about `0.62`. At 0.42 an
  11px label renders at 4.6px, which is unreadable today and worse with a denser card. Check the
  result at depth 3 before settling on a number.

## 4. The trap — measure the real DOM, not the geometry table

Node components set **`minHeight`, not `height`** (`nodes/StepNode.jsx:8-18`). Content can therefore
grow the DOM box past what the backend layout believes, and **nothing recomputes** — there is no
`ResizeObserver` and no use of `node.measured` anywhere in the frontend.

Everything downstream assumes the geometry-table height: `pushBelow` and `rectOf` in
`hooks/expansionBoxes.js:16-32,53-59`, `spaceSiblings` at `:61-75`, and the row maths in
`hooks/childPlacement.js:56-58`. A card that overflows its declared height produces **silent**
vertical collisions after a reveal, and dashed group boxes drawn shorter than their contents.

So: set the `NODE_GEOMETRY` heights large enough to contain the full card at every depth.

`scripts/flow_metrics.py` measures the geometry table and will therefore **not** catch an overflow.
`python scripts/flow_agent.py <repo> overlaps` reads `offsetWidth`/`offsetHeight` from the real DOM
(`scripts/flow_session.py:16-17,80-97`) and is the check that does. Run it at depth 3, not just on
the collapsed page.

## 5. Out of scope

- No changes to naming, prompts or the tracer pipeline — PBIs 63 and 64 own those.
- Do not add a "what's inside" preview of hidden children. It was considered and deferred.
- Do not remove `ProvenancePopover` — it still holds `backing` and the full multi-ref list, which do
  not fit on the face.
- Do not touch the top-level skeleton layout or `PillarGatewaySelector`.

## 6. Acceptance

- `python scripts/flow_agent.py <repo> --rebuild state overlaps` reports **0** overlaps on both
  django-helpdesk and CodeFlow, **and again after expanding a node and then one of its children**
  (depth 3).
- `python scripts/flow_metrics.py /tmp/hd` exits **0** with `roots 1, I5 0, I2 0, OVERLAPS 0`.
- Two-run determinism on `flow_graph.json` **and** `rendered_view.json`, both repos.
- `python scripts/selfrun.py` → 4/5, same single deliberate red.
- No `FALLBACK` geometry constant remains duplicated in any `nodes/*.jsx`.
- Every file touched ≤ 150 lines.

## 7. Look at the picture — this PBI is judged on the image

```
python scripts/screenshot_flow.py --save cooperkeenan /Users/cooperkeenan/github/django-helpdesk
python scripts/flow_agent.py /Users/cooperkeenan/github/django-helpdesk --rebuild \
  "toggle:<some entry>" "toggle:<one of its children>" overlaps fit "shot:scratch_out/p65_depth3.png"
```

Open both PNGs with the Read tool and answer directly:

1. Can you read the label, the summary and the `file:line` on every visible node **without
   zooming**?
2. At depth 3, is the text still legible, or has `MIN_SCALE` been set too low?
3. Does any card's text overflow its box, or any dashed group box clip its contents?
4. Does the canvas now feel used, or is it still mostly empty space?

Counts are not evidence. If the cards look cramped or the page now feels crowded, say so and
describe what you see — the sizes in §2 are a starting point, not a target to hit.
