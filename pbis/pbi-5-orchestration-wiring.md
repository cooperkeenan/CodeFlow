# PBI 5 — Orchestration & client wiring (API gateway)

**Depends on:** PBI 3 (layout emits template) and PBI 4 (render consumes it). **Read `README.md` first.**

## Why
Carry the chosen `DiagramTemplate` from the layout agent to the render agent, and the positioned React Flow JSON back through the gateway to the response — end to end.

## Scope

### 1. Render client — `api/clients/render_client.py`
- Change `render(...)` to send `{ "diagram_template": <DiagramTemplate dict> }` (plus `architecture_type` if still needed) and return the React Flow JSON (`{nodes, edges}`) instead of `response.json()["mermaid"]`.
- Keep the existing 5-attempt connect-retry loop and timeout.

### 2. Orchestration — `api/services/analysis_service.py`
- `_run_from_profile`: after `layout_result = await self._layout.layout(spec)`, pull `layout_result["diagram_template"]` and pass it to `self._render.render(...)`. Store the returned React Flow JSON.
- `analyse_from_trace`: mirror the change (it currently re-renders Mermaid from the stored trace — re-render React Flow JSON instead; the stored trace already carries the enriched spec / template if persisted).
- Add one `logger.info(...)` line in the existing stage-logging style for the chosen template type + node count.
- Replace the `mermaid` field usage in the returned response.

### 3. Models & artifacts
- `api/models/analysis_model.py`: `AnalyseResponse` carries the React Flow JSON (e.g. `diagram: {nodes, edges}`) and the chosen template type; drop/retain `mermaid` per the removal decision (default: drop).
- `OutputPersister`: replace the `render.mmd` artifact with `render.json` (the positioned graph). Keep `layout.json` (now includes `diagram_template`).

## Acceptance criteria
- A full `POST /analyse` returns positioned React Flow JSON for the system view plus the chosen template type.
- `analyse_from_trace` produces the same shape without re-running profiler/tracer.
- Persisted artifacts reflect the new output (`render.json`, `layout.json` with template).
- Gateway imports cleanly.

## Out of scope
- Frontend consumption (PBI 6).
