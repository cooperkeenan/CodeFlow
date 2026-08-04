# PBI 61 — Sequential decisions form one chain; pipelines render rigidly

From user review of a depth-2 reveal on django-helpdesk. Two defects and two presentation asks.
PBIs 57–60 are complete and accepted; do not redesign them.

**Frontend changes ARE authorized** — but only the files named in §3–§6.

Implement in the order below. **Verify §1 with `flow_metrics.py` before starting §2** — §1 changes
the graph and everything after it is rendering-only.

---

## 1. Consecutive single-path decisions are not linked (structure — tracer)

`dec:src.helpdesk.urls.<module>:56` ("UI feature enabled?") has `body_kind == "list"` and five
members, none connected to each other. But in source they are module-level `if` statements that
**execute in sequence**:

```
urls.py:27   if HELPDESK_KB_ENABLED:
urls.py:56   if HELPDESK_UI_ENABLED:
urls.py:224  if HELPDESK_API_ENABLED:
urls.py:264  if HELPDESK_KB_ENABLED:
```

Sequential execution is a real, statically-known fact. Dropping it is why the diagram shows five
scattered nodes joined by long curves instead of a pipeline, and why only **2 of 33** sequence
bodies on django-helpdesk currently form a chain.

**Change:** within a body, emit `kind="sequence"` edges linking consecutive members that are
single-path (`arm_count <= 1`) and share a scope, ordered by source position `(file, line)`. This is
static analysis recording execution order — the LLM must not be involved (CLAUDE.md: "Static
Analysis Owns Structure"). Do not link members separated by a real fork, and do not link across
different functions.

This will convert many `list` bodies into `flow` chains and populate their `body_head` /
`body_tails`. That is the intent.

**Verify before continuing:** `sequence bodies (N are chains)` in `flow_metrics.py` must rise
sharply from 2/33 on django-helpdesk. Report the before/after. Determinism must hold — sort every
iteration, tie-break on `(file, line, name)`.

## 2. Expanding a node breaks the chain (frontend)

Today when a node is expanded, its own incoming and outgoing edges stay attached to it, so the
revealed body hangs off to the side and the original edge bypasses it. The user's words:

> "You're expanding the chain so it should all stay connected instead of creating multiple chains
> when you drill down"

`body_head` and `body_tails` already exist on every node and are populated (99 heads, 187 tail sets
of 198 bodies) — use them, do not recompute.

**Change** in `frontend/src/hooks/useExpansion.js`:
- While node `N` is expanded and has a `body_head`: render each edge `X -> N` as `X -> body_head(N)`.
- While `N` is expanded and has `body_tails`: render each edge `N -> Y` (where `Y` is outside N's
  body) as `tail -> Y` for each tail.
- Suppress the original `X -> N` / `N -> Y` edges while expanded, so no bypass duplicate is drawn.
- A body with no `body_head` (a genuine fork, `body_kind == "list"`) keeps its current behaviour —
  the parent legitimately connects to all arms.

## 3. Linear runs render as a rigid pipeline (render + frontend)

Members of a linear run currently use the 3-per-row grid from `HiddenEmitter._block`, so a chain
scatters across rows and is joined by long curved edges. The user's ask:

> "make this diagram type a little more rigid, so it's circles that have the line connecting them
> to the previous and next one and use arrow heads"

**Change:**
- `shared/models/node_geometry.py` — add a `pipeline` geometry: a small circular marker with the
  label set beside it, so a run reads as a bullet list of things being done.
- `agents/render_agent/placement/flow_node_treatment.py` — `shape_for` returns `"pipeline"` for a
  node already flagged `linear` (PBI 60 added that flag) **when it is part of a run of 2 or more**;
  a lone linear node keeps `"rect"`.
- `frontend/src/hooks/useExpansion.js` — lay a run out in a single rigid column: constant x,
  constant row pitch, no per-row wrapping and no depth shrink within the run (PBI 60 already
  suppresses the shrink for linear children — extend it to runs of any length).
- New `frontend/src/components/flow/nodes/PipelineNode.jsx`, routed through `NodeChrome` like the
  other node kinds, registered in `FlowCanvas.jsx`, with `KIND_ACCENT` in `styles.js` and one row in
  `Legend.jsx`.

## 4. Edges have no arrowheads (frontend)

`FlowEdgeComponent.jsx` renders no marker of any kind — direction is currently unreadable.

**Change:** add an arrowhead marker at the target end. Apply it to all flow edges, not just
pipelines. Keep the existing stroke treatments (faded cross-link, dashed dynamic, gutter stitch)
intact — only the marker is new. Ensure the marker inherits the edge's colour and scales with the
edge's `scale`, and that it is legible in both light and dark themes.

## 5. Box overlay polish (frontend)

> "the box overlay could do with some improvement"

Group boxes still read as heavy overlapping slabs where they nest. In
`frontend/src/hooks/expansionBoxes.js` and `frontend/src/components/flow/nodes/GroupBox.jsx`:
- Increase the inset between a box and its nested child box so nesting depth is visible.
- Ensure a nested box never shares an edge line with its parent.
- Do not change `BOX_PAD` in a way that reintroduces node/box collisions — DOM overlaps must stay 0.

## 6. Out of scope

- Do not relabel decisions to imperative wording (needs a `PROMPT_VERSION` bump — tracked separately).
- Do not add invariants I4 or I7.
- Do not touch the top-level skeleton layout or `PillarGatewaySelector`.

## 7. Acceptance

- `flow_metrics.py` exits 0 on **both** django-helpdesk and CodeFlow with **roots 1, I5 0, I2 0,
  OVERLAPS 0**.
- `sequence bodies (N are chains)` rises sharply on both repos — report before/after.
- `python scripts/selfrun.py` → 4/5, same single deliberate red, no crash.
- Two-run determinism on `flow_graph.json` **and** `rendered_view.json`, both repos.
- DOM overlaps **0 at depth 3** via `flow_agent.py`, after expanding a node and then one of its
  children.
- Every file touched <= 150 lines.

## 8. Look at the picture — this PBI is judged on the image

```
python scripts/screenshot_flow.py --save cooperkeenan /Users/cooperkeenan/github/django-helpdesk
python scripts/flow_agent.py /Users/cooperkeenan/github/django-helpdesk --rebuild \
  "toggle:entry:seed:src.helpdesk.urls" "toggle:dec:src.helpdesk.urls.<module>:56" \
  overlaps fit "shot:scratch_out/p61_chain.png"
```

Open it with the Read tool and answer directly:
1. Do the five "feature enabled?" nodes read as **one connected pipeline** with arrowheads, or as
   scattered nodes joined by long curves?
2. Does the chain stay connected through the expanded node — i.e. does the incoming edge land on the
   first revealed node and the outgoing edge leave from the last?
3. Do any boxes or nodes overlap?

Counts are not evidence. If it still looks wrong, say so and describe what you see.
