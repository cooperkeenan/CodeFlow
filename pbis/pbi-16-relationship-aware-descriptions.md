# PBI 16 — Relationship-aware module descriptions (layout)

**Batch:** 4 &nbsp;|&nbsp; **Depends on:** PBI 15 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
Even with recovered edges, the system module-graph stays sparse, so the **descriptions** the
selector reads carry much of the signal. Today `build_evidence` describes each module with only
`{name, purpose (one sentence), zone_count}` — too thin for the LLM to tell pipeline from hub from
layered. Give it a richer, relationship-aware description (what the module does **and how it relates
to other modules**) without adding a new LLM call.

## Scope

### 1. Semantic enrichment — `agents/layout_agent/prompts/semantic_prompt.py`
Extend the existing semantic step so each module's output includes a 2–3 sentence description that
states the module's role and its relationships to other modules (consumes / produces / orchestrates
/ depends on). Keep the strict-JSON, no-markdown contract and the exact-name rules already in the
prompt. This reuses the existing semantic LLM call — **do not add a new call**.

### 2. Evidence payload — `agents/layout_agent/prompts/template_prompt.py`
In `build_evidence(...)`, replace the single `purpose` field per module with the richer description
from step 1, and add the module's **primary-component roles** (already available from the semantic
tier/role enrichment) so the LLM sees what kind of components each module contains. Keep the
module-edge and entry-point sections.

## Acceptance criteria
- Evidence JSON shows multi-sentence, relationship-aware module descriptions plus primary-component
  roles.
- No additional LLM call is introduced (semantic enrich count unchanged).
- Selection still runs at temperature 0.

## Out of scope
- The reasoning capture / `meta.rationale` work (PBI 17).
- Hint removal (PBI 14) and edge recovery (PBI 15).
