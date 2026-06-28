# PBI 4 — Rewire `TracerService` + config + DI

## Goal
Replace the monolithic whole-repo LLM call with the chunked, concurrent pipeline using the services
from PBI 1–3. Add config knobs and wire all DI.

## Read first
- `agents/tracer_agent/services/tracer_service.py` — current orchestrator (you rewrite `trace`; keep
  `_gather_evidence` + `_minimal_dirs` unchanged).
- The new services: `services/evidence_partitioner.py` (`EvidencePartitioner.partition(evidence,
  blueprint) -> list[EvidenceChunk]`), `services/chunk_context_builder.py`
  (`ChunkContextBuilder.build(blueprint, evidence) -> str`), `services/chunk_tracer.py`
  (`ChunkTracer.trace_chunk(chunk, context, blueprint, architecture_type) -> dict`),
  `services/raw_merger.py` (`RawMerger.merge(raws) -> dict`), `services/edge_recovery.py`
  (`EdgeRecovery.recover(spec, evidence) -> DiagramSpec`).
- `services/graph_validator.py` (`GraphValidator().validate(spec, evidence).fixed_spec`),
  `services/correction_prompt_builder.py`, `services/spec_assembler.py`,
  `services/component_placer.py`.
- `agents/tracer_agent/dependencies.py`, `agents/tracer_agent/core/config.py`.
- `CLAUDE.md` — standards (≤150 lines/file, constructor injection, type annotations, no comments/
  docstrings, no unused imports, no committed tests).

## 1. `core/config.py`
Add two settings to `Settings` with defaults:
```python
TRACER_CHUNK_TOKEN_BUDGET: int = 45000
TRACER_MAX_CONCURRENCY: int = 4
```
(They keep `extra="ignore"`, so `.env` need not define them.)

## 2. `services/tracer_service.py` — rewrite
New constructor (constructor injection only):
```python
def __init__(
    self,
    fetch_layer_files_tool: FetchLayerFilesTool,
    build_call_graph_tool: BuildCallGraphTool,
    build_evidence_tool: BuildEvidenceTool,
    spec_assembler: SpecAssembler,
    partitioner: EvidencePartitioner,
    context_builder: ChunkContextBuilder,
    chunk_tracer: ChunkTracer,
    raw_merger: RawMerger,
    edge_recovery: EdgeRecovery,
    graph_validator: GraphValidator,
    max_concurrency: int,
) -> None: ...
```
New `trace`:
```python
async def trace(self, request: TracerRequest) -> TracerResponse:
    evidence = await self._gather_evidence(request)
    chunks = self._partitioner.partition(evidence, request.blueprint)
    context = self._context_builder.build(request.blueprint, evidence)
    semaphore = asyncio.Semaphore(self._max_concurrency)

    async def _run(chunk: EvidenceChunk) -> dict:
        async with semaphore:
            return await self._chunk_tracer.trace_chunk(
                chunk, context, request.blueprint, request.architecture_type
            )

    raws = await asyncio.gather(*[_run(c) for c in chunks])
    merged = self._raw_merger.merge(list(raws))
    spec = self._assembler.assemble(request.blueprint, merged, request.architecture_type)
    spec = self._edge_recovery.recover(spec, evidence)
    spec = self._graph_validator.validate(spec, evidence).fixed_spec
    # keep the existing component/edge-count logging block, operating on `spec`
    return TracerResponse(architecture_type=request.architecture_type, diagram_spec=spec)
```
- Keep `_gather_evidence` and `_minimal_dirs` exactly as they are.
- **Delete** `_call`, `_sanitise`, `_correction_loop`, `_user_prompt` (moved to `ChunkTracer`).
- Keep the existing `logger.info("Trace: modules=… components=… edges=… …")` summary (recompute over
  the final `spec`). Add one `logger.info` line reporting the chunk count, e.g.
  `logger.info("Tracing %s in %d chunks", request.repo_name, len(chunks))`.
- **Remove now-unused imports** (`anthropic`, `MessageParam`, `re`, `TRACER_SYSTEM_PROMPT`,
  `CorrectionPromptBuilder` if no longer referenced) and add `asyncio` + the new service imports.
- The service no longer holds the `anthropic` client directly (the `ChunkTracer` does).

## 3. `dependencies.py` — wire everything
Add factories and inject (constructor injection via `Depends`):
- `get_evidence_partitioner(placer = Depends(get_component_placer), settings = Depends(get_settings)) -> EvidencePartitioner` → `EvidencePartitioner(placer, settings.TRACER_CHUNK_TOKEN_BUDGET)`.
- `get_chunk_context_builder() -> ChunkContextBuilder`.
- `get_raw_merger() -> RawMerger`.
- `get_edge_recovery() -> EdgeRecovery`.
- `get_graph_validator() -> GraphValidator`.
- `get_correction_prompt_builder() -> CorrectionPromptBuilder`.
- `get_chunk_tracer(anthropic_client = Depends(get_anthropic_client), spec_assembler = Depends(get_spec_assembler), graph_validator = Depends(get_graph_validator), correction_builder = Depends(get_correction_prompt_builder)) -> ChunkTracer`.
- Rewrite `get_tracer_service` to inject: the three evidence tools (as today), `spec_assembler`,
  `partitioner`, `context_builder`, `chunk_tracer`, `raw_merger`, `edge_recovery`, `graph_validator`,
  and `settings.TRACER_MAX_CONCURRENCY` (add `settings = Depends(get_settings)`).

## Acceptance / verification
- `tracer_service.py`, `dependencies.py`, `config.py` parse; `tracer_service.py` ≤150 lines; no unused
  imports anywhere touched.
- **End-to-end smoke (real LLM, small repo):** with the tracer service constructed via the same
  manual wiring used previously (or by starting the agent), run a trace over the cached profile for a
  small repo and confirm: `HTTP 200`-equivalent success, `diagram_spec` has a sensible component/edge
  count, and the logs show the chunk count. A throwaway in-process script is fine (build the full
  object graph: `ComponentPlacer`, `SpecAssembler(placer)`, `EvidencePartitioner(placer, budget)`,
  `ChunkContextBuilder`, `ChunkTracer(anthropic, assembler, GraphValidator(), CorrectionPromptBuilder())`,
  `RawMerger`, `EdgeRecovery`, `GraphValidator`, then `TracerService(...).trace(request)`).
  Use `LOCAL_REPO_PATH` from `.env`, repo root + `agents/tracer_agent` on `sys.path`, cwd at
  `agents/tracer_agent`, `load_dotenv`. Delete the temp script after.
- Force a tiny `TRACER_CHUNK_TOKEN_BUDGET` (e.g. 2000) in the throwaway to confirm multiple chunks are
  produced and the trace still assembles a coherent spec.

## Out of scope
Gateway/httpx timeout changes. Frontend. Profiler.
