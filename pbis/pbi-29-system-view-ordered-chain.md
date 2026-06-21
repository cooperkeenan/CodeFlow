# PBI 29 — System view honors type-aware edges (ordered chain)

**Batch:** 8 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
The system view is *typed* `pipeline` but still renders as a hub: nodes in alphabetical order and
edges still `api → each agent`. Batch 7's type-aware edge builder lives in
`agents/layout_agent/services/_view_builder.py`, but the **system template is built on a different
path** (`TemplatePlanner` / the `select_diagram_template` tool / `ViewPlanner.plan` for the system
view), so it never gets the chain treatment.

## Scope
- Route the system template through the same type-aware edge builder (`_edge_builder.py`, Batch 7) so
  a `pipeline` system view produces an ordered chain instead of the raw hub edges.
- **Order** the system pipeline by `layout_hint.module_order` (already computed by `LayoutService`),
  not alphabetically. Other types keep their current edges (hub stays `hub→spoke`, etc.).
- Touch the system-template construction in `ViewPlanner` / `TemplatePlanner` only; do not change the
  module/component paths (already handled by Batch 7).

## Acceptance criteria
- A `pipeline` system view shows the modules in `module_order` as a left→right chain; dragging the
  nodes keeps it a chain (no star edges).
- If the system is typed `hub_and_spoke`, it still renders hub→spoke. Determinism at temperature 0.

## Out of scope
- Side-handle routing (PBI 28). The service-centric abstraction (Batch 9).
