# PBI 30 — Harden the component-type selector (no silent total fallback)

**Batch:** 9 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
The Batch 6 component-type LLM selector silently reverts the **entire** component layer to the
deterministic topology classifier whenever its one batched call hiccups — so `TracerService` (6
callees) goes back to `hub_and_spoke` and the rich rationale disappears. Confirmed on the current run:
**0 of 47 component views have a rationale**, and the type split is exactly the classifier's output.

Root cause in `agents/layout_agent/services/component_type_planner.py`:
- **One batched call, all-or-nothing**: `plan()` wraps `_call` + `_validate` in `try/except` and
  `return {}` on any error — a single bad/oversized response zeroes out every component.
- **Truncation**: `_call` uses `max_tokens=4000` and `re.search(r"\{.*\}")`; the batched response
  (type + reasoning + `order` array for every high-level component) overflows 4000 tokens, the JSON is
  unbalanced, `json.loads` throws → caught → `{}`. PBI 24's richer descriptions made this worse.
- **Silent**: the only signal is a buried `logger.exception("…using classifier fallback")`.

## Scope — `agents/layout_agent/services/component_type_planner.py`
- **Stop truncating**: raise `max_tokens` and/or **chunk** the batched call (e.g. per module, or N
  components per call) so a response can't overflow. Merge the chunks' results.
- **Not all-or-nothing**: keep every valid component entry; fall back to the deterministic classifier
  **only for the components actually missing/invalid**, not the whole set. A parse failure on one
  chunk must not drop the others.
- **Robust parse**: tolerate markdown fences / trailing prose; if a chunk's JSON is unparseable, skip
  just that chunk.
- **Surface failures**: when any component falls back, log it loudly (count of fell-back components)
  rather than burying a single exception — a total fallback must be visible, not silent.

## Acceptance criteria
- `component:TracerService` is `pipeline` again, with a populated `meta["rationale"]`.
- If the LLM partially fails, only the affected components fall back; the rest keep their LLM types.
- A run where selection fully fails logs an explicit, countable warning (not a silent revert).
- Deterministic at temperature 0.

## Out of scope
- Module-level type selection (PBI 31). The service abstraction (Batch 10).
