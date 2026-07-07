# PBI 34 — Capture component source line ranges (tracer)

**Batch:** 11 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
The new click-to-view-code feature must scroll a file to where a component is defined, but
**no line numbers are captured anywhere** in the pipeline. The tracer already AST-parses
every analyzed file (`agents/tracer_agent/services/ast_service.py`), and `ast.ClassDef`
nodes expose `.lineno` / `.end_lineno`. We capture these **deterministically** (no LLM —
matches the facts-vs-interpretation principle) and attach them to each `Component`, so they
flow unchanged through layout/render to `trace.diagram_spec` on the frontend.

## Scope

### 1. Model — `shared/models/diagram_spec.py`
Add to `Component` (backward-compatible, optional):
```python
start_line: int | None = None
end_line: int | None = None
```

### 2. AST capture — `agents/tracer_agent/services/ast_service.py`
In `extract_signatures`, add `start_line` / `end_line` to each class entry from
`node.lineno` / `node.end_lineno`. Each entry already carries `file_path`, so the
`signatures` dict doubles as the per-class location map.

### 3. Enrichment — `agents/tracer_agent/services/line_range_enricher.py` (new)
One class, constructor-injected, ≤150 lines. Given the assembled `DiagramSpec` and the
`signatures` map, set `start_line`/`end_line` on every component whose `name` matches a
signature entry **with the same `file_path`** (guard against same-named classes in
different files). Leave ranges `None` when no match.

### 4. Wire it — `agents/tracer_agent/services/tracer_service.py`
Inject `LineRangeEnricher`; call it in `trace()` after `_assembler.assemble(...)` (the
`signatures` live in `evidence`, already in scope). Register in the tracer's
`dependencies.py`.

## Acceptance criteria
- After `/analyse`, `outputs/tracer.json` components carry integer `start_line`/`end_line`
  for classes the AST resolved; unresolved components have `null` and do not crash.
- Two runs on the same repo give identical ranges (deterministic).
- Layout/render output and `diagram_spec` shape are otherwise unchanged.

## Out of scope
- Standalone-function components (only `ClassDef` ranges this batch — note as future).
- Any storage or frontend work (PBIs 35–37).
