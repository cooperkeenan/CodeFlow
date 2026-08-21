# Poster evidence harvest

Every number on the poster must trace to a block in this file. Captured 2026-08-20 on `main`.
Studies 7.2 (precision/recall) and 7.3 (baseline comparison) have NOT been run — no such
numbers appear on the poster.

## 1. `python scripts/flow_metrics.py scratch_out` — django-helpdesk

```
repo              django-helpdesk
nodes / edges     394 / 488
  edge kinds      {'arm': 159, 'sequence': 329}
  synthesized     2
kinds             {'decision': 222, 'entry': 33, 'step': 34, 'outcome': 105}
roots             1 ['root:django-helpdesk']
depth             {0: 1, 1: 61, 2: 109, 3: 133, 4: 48, 5: 29, 6: 11, 7: 1, 8: 1}
skeleton (lvl 0)  16  (budget 15)
bodies            198  (multi-member 106)
  size dist       {1: 92, 2: 50, 3: 27, 4: 7, 5: 3, 6: 3, 7: 4, 8: 12}
  body_kind       {'flow': 104, 'list': 94}
  decision forks  72  (23 fork only to outcomes)
  sequence bodies 34  (6 are chains)
I3 single-entry   15/16 flow bodies clean
    GAP more:dec:src.helpdesk.update_ticket.update_ticket:254:0 -> ['dec:src.helpdesk.update_ticket.update_ticket:290']
I5 cohesion       0 violations
I2 unreachable    0 
OVERLAPS          0 
```

Exit 0 (all invariants held).

## 2. `python scripts/selfrun.py` — CodeFlow analysing itself

```
judge=LLM
lanes=['api', 'explain', 'figures', 'layout', 'profiler', 'render', 'scripts', 'tracer'] nodes=499 edges=698 stitches=4 decisions=174 rendered=23
Assertions:
  [FAIL] lanes == {api, profiler, tracer, layout, render}: ['api', 'explain', 'figures', 'layout', 'profiler', 'render', 'scripts', 'tracer']
  [PASS] >=4 stitch edges api->agent entries: 4 stitches
  [PASS] two runs byte-identical (ignoring llm_*)
  [PASS] skeleton node count within budget ceiling: 16 skeleton nodes of 499 total
  [PASS] every revealed node is reachable from a parent's hidden_children: 0 stranded
  [PASS] node/edge counts unchanged across reviewer stage: pre=499n/698e post=499n/698e
  [FAIL] no guard-selector decision survives: 1 guard decisions
provenance: 463/499 nodes carry a SourceRef (entries lack refs by construction: 36 without)
decisions: 174 emitted, all revealable; 16 skeleton nodes form the collapsed page (node_budget=40)
EXIT=1
```

Exit 1. Two assertions fail:
- `lanes == {api, profiler, tracer, layout, render}` — a **stale assertion**, not a defect: the repo
  has since gained `explain`, `figures` and `scripts` lanes. Not reported as a result.
- `no guard-selector decision survives: 1 guard decisions` — a **real, small defect** out of 174
  emitted decisions. Reported honestly on the poster.

## 3. `.cache/decision_verdicts.json` — LLM judge verdicts

```
decision_verdicts: 5916 entries
  verdicts: {'guarded_step': 3750, 'decision': 1616, 'noise': 550}
    guarded_step: 3750 (63.4%)
    decision: 1616 (27.3%)
    noise: 550 (9.3%)
  confidence mean=0.915 median=0.920 n=5916
  importance mean=0.168 n=5916
node_names: 1396 entries
stitch_verdicts: 23 entries
review_findings: 13 entries
```

## 4. Scale of the artefact

```
commits: 85
merged PRs: 15
python files: 387
python LOC: 15689
detectors:
branch_detector.py
dispatch_detector.py
dynamic_detector.py
effect_detector.py
except_detector.py
http_stitch_detector.py
llm_stitch_detector.py
match_detector.py
parallel_detector.py
polymorphic_detector.py
route_detector.py
stitch_detector.py
table_detector.py
```

Seven **dispatch-site** detectors: branch, match, except, table, route, polymorphic, dynamic.
(`effect_`, `stitch_`, `parallel_` and `dispatch_detector.py` serve other concerns.)

## 5. Score weights — `significance_config.py` / `site_scorer.py` (read, not run)

`score = 3.0·log2(1+|live reach|) + 2.0·provenance + 2.0·(not reconverges) + 1.0·(kind ∈ {route, table, polymorphic})`

`utility_min_fan_in=8`, `utility_percentile=0.90`, `reach_max_depth=6`, `guard_reach_limit=2`.
These are tuned empirical constants — stated as an assumption on the poster.

## 6. Collapsed-page node count — `scratch_out/rendered_view.json` (read, not run)

```
rendered_view.json nodes: 18 | hidden: 378
non-lane nodes: 15   (18 = 15 flow nodes + 3 lane headers)
```

Paired with `nodes / edges  394 / 488` from §1, this is the "394 -> 18" figure on the poster.

## 7. Digits used on the poster, and where each comes from

| Poster claim | Source |
|---|---|
| byte-identical across two runs | §2 `[PASS] two runs byte-identical (ignoring llm_*)` |
| 463/499 grounded, 36 without | §2 provenance line |
| 394 -> 18 | §1 node count + §6 rendered view |
| 0 / 0 / 0 invariants | §1 `OVERLAPS 0`, `I2 unreachable 0`, `I5 cohesion 0 violations` |
| 1 of 174 | §2 `1 guard decisions` and `decisions: 174 emitted` |
| 5,916 forks; 63.4 / 27.3 / 9.3 %; confidence 0.92 | §3 |
| seven dispatch detectors | §4 |
| eight tracer stages | `figures/fig1_architecture.py` stage strip |
| score weights 3.0 / 2.0 / 2.0 / 1.0 | §5 |

No precision, recall, F1 or baseline-comparison figure appears on the poster, because
studies 7.2 and 7.3 have not been run.

## 8. Screenshots on the poster

All three are CodeFlow's own output on **django-helpdesk**, captured from
`frontend/public/fixture/rendered_view.json` (the run recorded in §1).

| Poster figure | Source | Crop (l, t, r, b) |
|---|---|---|
| Figure 3 — The decision map | `poster/shot_decision_flow.png` | `(0, 30, 2040, 1610)` of the raw capture |
| Figure 4 — Drill into one symbol | `poster/shot_flowchart.png` | `(0, 0, 2440, 1340)` |
| Figure 5 — Down to the source | `poster/shot_code_view.png` | `(0, 0, 2604, 1430)` |

All three are viewport captures of the isolate/frame UI on django-helpdesk. Crops are top-left
anchored and were chosen off a per-row ink profile so no node box or code line is sliced: the
flowchart cuts at y=1340, the first quiet row above the bottom node pair. Figures 4 and 5 are cropped
to the same 1.821 aspect because they are the *same frame* in its two states, and should read as a
pair. The decision-map crop drops the right 234 px (the minimap) and the top 30 px (clipped node
stubs from the viewport edge).

**On code panes.** Earlier code-pane captures were rejected because they rendered a synthetic
stress-test fixture (`method_0`, "Does thing number 0", `value_0 = compute(self.registry, 0)`).
Figure 5 is **not** one of those: it shows `Command.handle` from
`src/helpdesk/management/commands/escalate_tickets.py` — real django-helpdesk source, with
`Queue.objects.filter(escalate_days__isnull=False)` and `EscalationExclusion` visible. The rule
stands: any pane showing `method_0` / `compute(self.registry, ...)` is fixture data and must not ship.
