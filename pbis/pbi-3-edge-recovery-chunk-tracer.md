# PBI 3 — `EdgeRecovery` + `ChunkTracer`

## Goal
Add two services the chunked tracer (PBI 4) will use: a deterministic post-merge edge recovery, and a
single-chunk LLM tracer with bounded per-chunk self-correction. No wiring into `TracerService` yet.

## Read first
- `agents/tracer_agent/services/tracer_service.py` — `_call` (lines ~83-93), `_sanitise`
  (~95-105), `_correction_loop` (~107-122), `_user_prompt` (~124-135). You are lifting `_call`/
  `_sanitise` and the correction pattern into `ChunkTracer`.
- `agents/tracer_agent/services/spec_assembler.py` (now takes a `ComponentPlacer`),
  `services/graph_validator.py` (`GraphValidator.validate(spec, evidence) -> ValidationResult` with
  `.correctable_warnings`, `.fixed_spec`), `services/correction_prompt_builder.py`
  (`CorrectionPromptBuilder().build(validation, attempt) -> str`).
- `prompts/tracer_prompt.py` (`TRACER_SYSTEM_PROMPT`), `shared/models/diagram_spec.py`
  (`DiagramSpec`, `Edge`), `shared/models/repo_blueprint.py`.
- `CLAUDE.md` — standards (≤150 lines/file, constructor injection, type annotations, no comments/
  docstrings/logging churn beyond what these methods already log, no tests, no unused imports).

## 1. `agents/tracer_agent/services/edge_recovery.py`
```python
class EdgeRecovery:
    def recover(self, spec: DiagramSpec, evidence: dict) -> DiagramSpec: ...
```
- Build `names = {c.name for m in spec.modules for cs in m.zones.values() for c in cs}` and
  `existing = {(e.source, e.target) for e in spec.edges}`.
- For each `ce` in `evidence.get("confirmed_edges", [])` with `ce["from"]` and `ce["to"]` both in
  `names` and `(ce["from"], ce["to"]) not in existing`: append `Edge(source=ce["from"],
  target=ce["to"], edge_type="call")` (also add to `existing` to avoid dups within the loop).
- Return `spec.model_copy(update={"edges": [...spec.edges, ...recovered]})`. Pure; no LLM.

This recovers **cross-module in-process call edges** a single chunk cannot emit (it never sees other
modules' signatures). `confirmed_edges` are facts (import ∩ call-graph), so adding them by rule is
sound.

## 2. `agents/tracer_agent/services/chunk_tracer.py`
```python
class ChunkTracer:
    def __init__(
        self, anthropic_client, spec_assembler, graph_validator, correction_builder,
    ) -> None: ...
    async def trace_chunk(
        self, chunk: EvidenceChunk, context: str, blueprint: RepoBlueprint, architecture_type: str,
    ) -> dict: ...
```
Behavior:
- Build the user prompt: the shared `context` string + `"\n\nEVIDENCE BUNDLE:\n" +
  json.dumps(chunk.evidence)`. Seed `messages = [{"role": "user", "content": user_prompt}]`.
- `raw = await self._call(messages)` — lift `_call`/`_sanitise` from `TracerService` verbatim
  (`messages.create(model=_MODEL, max_tokens=10000, temperature=0, system=TRACER_SYSTEM_PROMPT,
  messages=messages)`, regex-extract the JSON object, sanitise). Keep `_MODEL =
  "claude-haiku-4-5-20251001"`.
- **Bounded self-correction (≤2 rounds), scoped to this chunk's evidence:**
  ```
  for attempt in range(1, 3):
      spec = self._assembler.assemble(blueprint, raw, architecture_type)
      validation = self._validator.validate(spec, chunk.evidence)
      if not validation.correctable_warnings or attempt == 2:
          break
      correction = self._correction_builder.build(validation, attempt)
      messages.append({"role": "assistant", "content": [{"type": "text", "text": json.dumps(raw)}]})
      messages.append({"role": "user", "content": correction})
      raw = await self._call(messages)
  ```
  Validating against `chunk.evidence` (not the whole repo) keeps each correction prompt small. Cross-
  module gaps are handled later by `EdgeRecovery`, not here.
- Return the final `raw` dict (merging happens on raws in PBI 4 via `RawMerger`). Do not assemble for
  the return value.

`EvidenceChunk` is imported from `services.evidence_partitioner` (PBI 2).

## Acceptance / verification
- Both files parse, ≤150 lines, no unused imports.
- `EdgeRecovery` throwaway check (no LLM, don't commit): take the stored `diagram_spec` +
  the evidence's `confirmed_edges`; remove one confirmed edge from the spec; assert `recover` re-adds
  exactly that edge as `edge_type="call"` and adds nothing whose endpoints aren't components.
- `ChunkTracer` is exercised end-to-end in PBI 4; here just confirm it imports and constructs with the
  real dependencies (a smoke import is enough — do not burn an LLM call).

## Out of scope
No changes to `tracer_service.py`, `dependencies.py`, or config (PBI 4). No partitioner/merger changes.
