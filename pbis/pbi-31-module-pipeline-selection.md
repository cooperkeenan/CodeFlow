# PBI 31 — Let module views be pipelines (de-bias the cluster planner)

**Batch:** 9 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
The module view (e.g. `tracer_agent`) is always `hub_and_spoke` because the cluster-planner prompt
biases to hub on fan-out — `cluster_prompt.py`: *"hub_and_spoke: one orchestrator fans out to many
services"* — and `TracerService` has `fan_out: 6`. But a module whose orchestrator runs its services
**in sequence** is a pipeline, just like the component view already concluded. The module level needs
the same semantics-over-topology treatment.

## Scope — `agents/layout_agent/prompts/cluster_prompt.py` (+ `services/cluster_planner.py`)
- Refine the `diagram_type` guidance so a module is `pipeline` when its orchestrator drives its
  services **in a sequence** (data flows step→step), and `hub_and_spoke` only when the spokes are
  genuinely independent (no ordering, parallel handlers). High fan-out alone must not force hub.
- Give the planner the signal to decide: include the orchestrator's purpose/description and (if
  available) its ordered steps in the module evidence, mirroring how the component selector reasons.
- A `pipeline` module must reuse the Batch 7 `_edge_builder` chain so it renders as an ordered
  left→right flow (this path already exists for structural modules).

## Acceptance criteria
- `module:tracer_agent` can be typed `pipeline` (with an ordered chain) when its orchestrator is
  sequential; modules with genuinely independent spokes stay `hub_and_spoke`; `zoned` modules
  unaffected.
- Selection remains deterministic at temperature 0.

## Out of scope
- The component-selector hardening (PBI 30). The service abstraction (Batch 10).
