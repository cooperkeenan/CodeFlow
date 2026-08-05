# PBI 62 — Refactor: delete dead code, remove triplication, refresh the docs

Housekeeping pass after PBIs 57–61. **Behaviour-preserving**: this PBI must not change a single
byte of pipeline output. Everything below was measured, not guessed — do not re-derive it.

---

## 1. Delete verified dead code

Both confirmed to have **zero** references anywhere in `agents/`, `shared/`, `scripts/`, `api/`,
`frontend/src`:

- `agents/tracer_agent/services/analysis/spine_protector.py` (33 lines, class `SpineProtector`) —
  orphaned when the budget pipeline was rewritten.
- `frontend/src/components/Badge.jsx` — the only `Badge` usage in the app is `NodeBadges.jsx`,
  which does not import this file.

Delete both. Confirm with a repo-wide grep afterwards that nothing referenced them.

## 2. Do NOT delete the editable-diagram slice

`api/routers/diagram_edits.py` is not mounted in `api/main.py`, and no page imports
`EditToolbar.jsx` / `useEditableCanvas.js`. The whole slice (~582 lines across router, service,
store protocol, Neon store, `useDiagramEdits.js`, `api/diagrams.js`, `edgeMarkers.js`, toolbar,
canvas) is currently unreachable.

**The user has decided to wire it up in a later PBI.** Leave every one of those files exactly as
they are. Document the state in HANDOFF.md (§4 below) so it is not mistaken for dead code again.

## 3. Remove the triplicated container-repoint logic (SOLID)

`_repoint_containers` and its `_is_descendant` cycle guard are implemented **three times**, nearly
character-identical:

- `agents/tracer_agent/services/analysis/budget_recondenser.py` (`source`/`target`, `BudgetWorkGraph`)
- `agents/tracer_agent/services/analysis/effect_capper.py` (`keep`/`other`, `BudgetWorkGraph`)
- `agents/tracer_agent/services/analysis/step_merger.py` (`source`/`target`, plain `dict` of drafts)

**Change:** extract one `ContainerRepointer` into a new
`agents/tracer_agent/services/analysis/container_repointer.py` with a single method that takes a
mapping of `id -> object exposing .containers`, plus the source and target ids. Because
`StepMerger` operates on draft dicts and the other two on `BudgetWorkGraph.nodes`, the collaborator
must depend only on that minimal mapping interface — not on `BudgetWorkGraph` (Interface
Segregation / Dependency Inversion).

Inject it via constructor into all three (constructor injection only, per CLAUDE.md), and update
their factories. Delete the three private copies. The cycle guard must keep behaving identically —
it is load-bearing and was added to fix real containment cycles.

## 4. Split the one file over the 150-line cap

`agents/tracer_agent/services/evidence/file_fetch_service.py` is **164 lines** — the only file in
the repo over the cap. Split along a genuine responsibility seam; do not just move lines to make the
number pass. Every resulting file <= 150 lines.

## 5. Documentation

### `HANDOFF.md` (currently 557 lines, 13 sections, largely accumulated history)
Rewrite it to describe the **current** state, not the journey. It should read as an orientation doc
for a fresh session. Cover:
- The containment model as it now stands: `containers`, `hidden_children`, `body_kind`,
  `body_head`, `body_tails`, `level` = containment depth.
- **I3 is a derivation rule for `body_kind`, not an assert.** Asserting it crashed the pipeline on
  CodeFlow's own repo, because a shared memoized node can be both the predecessor of a body member
  and a containment ancestor of that body via a different path. I1 (DAG) and I2 (total reachability)
  and I5 (cohesion) ARE hard asserts.
- **The flow/list ratio is not a quality metric.** A decision's arms are mutually exclusive
  alternatives, so a fork is correctly `list`. Judge forks and chains separately — that is what
  `scripts/flow_metrics.py` prints.
- `scripts/flow_metrics.py` as the standard verification harness.
- The editable-diagram slice: built, currently unwired, to be wired in a later PBI (§2 above).
- Honest open defects, with the real numbers:
  - top level is 18 nodes with essentially one edge between them — the biggest visible weakness;
  - `PillarGatewaySelector` scores `entry:group:*` route groups 0 because they lack `backing`, so
    they lose skeleton slots to less central `entry:seed:*` anchors;
  - chunked bodies can be `body_kind == "flow"` with `body_head == None`, which silently disables
    the PBI 61 chain re-routing for those bodies (one case on django-helpdesk);
  - single-path decisions render as commands but are still labelled as questions (needs a
    `PROMPT_VERSION` bump);
  - `sequence bodies`: only 5 of 33 form chains on django-helpdesk, 18 of 69 on CodeFlow.

Cut the historical "was → now" narrative. Length is not the target — accuracy and usefulness are —
but expect it to get substantially shorter.

### `CLAUDE.md`
- Add `scripts/flow_metrics.py` to the verification loop alongside `screenshot_flow.py` and
  `flow_agent.py`, stating it must exit 0 and what it prints.
- Add a short rule capturing the metric trap: *a falling flow/list ratio is not a regression; judge
  forks and chains separately, and settle it by opening the PNG.*
- Keep every existing rule. Do not weaken "Do Not Weaken Checks To Go Green", the 150-line cap, the
  no-hardcoding rule, or the determinism section.

### `PROMPT.md`
Update the pipeline description to include the stages added since it was written: `ContainmentIndexer`,
`OutcomeLabeler`, `DecisionProjector`, `SequenceChainer`, `ContainerRepointer`, and the
`outcome` / `pipeline` node kinds. Keep it a context primer — do not let it grow into a second
HANDOFF.

## 6. Acceptance — behaviour must be identical

Baselines are saved. The refactor is only correct if output is byte-identical:

```
source venv/bin/activate
python scripts/render_repo.py /Users/cooperkeenan/github/django-helpdesk /tmp/hd
diff -q /tmp/hd/flow_graph.json    /tmp/rf_hd_graph.json
diff -q /tmp/hd/rendered_view.json /tmp/rf_hd_view.json
python scripts/render_repo.py . /tmp/cf
diff -q /tmp/cf/flow_graph.json    /tmp/rf_cf_graph.json
diff -q /tmp/cf/rendered_view.json /tmp/rf_cf_view.json
```

All four diffs must be silent. **Exception:** CodeFlow analyses its own source, so deleting
`spine_protector.py` and adding `container_repointer.py` will legitimately shift `/tmp/cf` node ids.
If `/tmp/cf` differs, prove the delta is confined to renamed/line-shifted ids by checking node count,
edge count and the `kind` multiset are unchanged — and report it. `/tmp/hd` (django-helpdesk) must
be **exactly** byte-identical with no exceptions; it does not analyse CodeFlow's source.

Also required:
- `python scripts/flow_metrics.py /tmp/hd` and `/tmp/cf` exit 0.
- `python scripts/selfrun.py` → 4/5, same single deliberate red, no crash.
- No file in the repo over 150 lines.
- No unused imports introduced (`python -m pyflakes agents shared scripts api` stays clean).
- Do not add tests. Do not "improve" behaviour anywhere — anything that changes output is a bug in
  this PBI.
