# PBI B — Extract component view builder + service-centric contraction + drill-down

## Goal
Make the high-level component view surface **services** (not thin tool wrappers), and make drilling
into a service show a **bordered container** with its wrapper folded in. Because
`_view_builder.py` is already 148/150 lines, first **extract** `build_component` into a new module,
then add the new logic there.

## Background (root cause)
For `component:TracerService` (role `orchestrator`), the focus's direct callees/children are the thin
wrappers `BuildCallGraphTool`, `BuildEvidenceTool`, `FetchLayerFilesTool`. The real services
(`CallGraphService`, …) are one hop deeper, so the old inline contraction never folds them and the UI
shows tool→tool. PBI A added a pure helper (`agents/layout_agent/services/_neighborhood.py`) that
fixes the graph reasoning. This PBI wires it in.

Read first:
- `agents/layout_agent/services/_neighborhood.py` (PBI A — the helper you will call).
- `agents/layout_agent/services/_view_builder.py` (current `build_component` you will move).
- `agents/layout_agent/services/_container_builder.py` (`build_container`, reused as-is).
- `agents/layout_agent/services/_edge_builder.py` (`build` aliased `_build_type_edges`).
- `agents/layout_agent/services/view_planner.py` (constructs `_ViewBuilder`, calls
  `self._builder.build_component(...)` — its call sites must keep working unchanged).
- `CLAUDE.md` (standards: ≤150 lines/file, constructor injection, type annotations, no comments/
  docstrings/logging/tests, no unused imports).

`_neighborhood.py` public API:
```python
def single_callee_adapters(names, all_comps, edges) -> dict[str, str]
@dataclass class ContractedSteps: callees: list[str]; children: list[str]; folded: dict[str, list[str]]
def contract_steps(focus, callees, children, all_comps, edges) -> ContractedSteps
@dataclass class WrappedFocus: folded: list[str]; pulled_callers: list[str]
def wrapping_adapters(focus, callers, all_comps, edges) -> WrappedFocus
```

## Step 1 — Extract `build_component` into a new module
Create `agents/layout_agent/services/_component_view_builder.py` with a single class
`_ComponentViewBuilder` (constructor injection of the classifier), holding the relocated
`build_component` logic as a method named `build`:
```python
class _ComponentViewBuilder:
    def __init__(self, classifier: ComponentArchetypeClassifier) -> None:
        self._classifier = classifier
    def build(self, spec: DiagramSpec, component_name: str, view_set: set[str],
              comp_types: dict | None = None) -> DiagramTemplate: ...
```
Move all imports it needs (`build_container`, `_build_type_edges`, `TemplateNode`, `TemplateEdge`,
`DiagramTemplate`, `DiagramSpec`, etc.) into this new file.

In `_view_builder.py`:
- Remove the `build_component` method, the now-unused `contract` import (keep `bfs_depth`), and the
  `build_container` import (it moves to the new file). Keep `build_module` and
  `_build_structural_module` exactly as-is.
- `_ViewBuilder.__init__` constructs `self._component_builder = _ComponentViewBuilder(classifier)`.
- Add a thin delegating method so existing callers keep working:
  ```python
  def build_component(self, spec, component_name, view_set, comp_types=None) -> DiagramTemplate:
      return self._component_builder.build(spec, component_name, view_set, comp_types)
  ```
- `view_planner.py` must remain unchanged.

After extraction, both `_view_builder.py` and `_component_view_builder.py` must be ≤150 lines.

## Step 2 — New behavior inside `_ComponentViewBuilder.build`
Keep the existing head (build `comp_to_mod`, `all_comps`, `focused`, the `callers`/`callees`/
`children` derivation — lines ~97-114 of the current method). Then replace the old contraction block
(old lines ~115-123, the `focused.role in {...}` inline `_s`/`_er`/`contract` block **and** the
`if folded_map: return build_container(...)` early return) with the following two pieces:

### 2a — Drill-down container (focus is wrapped by thin adapters)
Immediately after computing `callers/callees/children`:
```python
wf = wrapping_adapters(component_name, callers, all_comps, spec.edges)
if wf.folded:
    return build_container(
        component_name, wf.pulled_callers, callees, children,
        {component_name: wf.folded}, comp_to_mod, view_set,
    )
```
This makes `component:CallGraphService` render `TracerService → [container: BuildCallGraphTool +
CallGraphService]`.

### 2b — High-level surfacing (fold wrappers among the steps into their services)
```python
folded_map: dict = {}
if focused.role in _PRIMARY:
    cs = contract_steps(component_name, callees, children, all_comps, spec.edges)
    callees, children, folded_map = cs.callees, cs.children, cs.folded
```
Use the `_PRIMARY` frozenset imported from `services._graph_contraction` (same set the old code
spelled out: `{"service", "orchestrator", "repository", "entry"}`). Do **not** route this to
`build_container`; fall through to the existing classifier + edge path so the LLM-chosen diagram
type/order still applies — now over the service node set.

### 2c — Synthetic connectivity for folded survivors
The literal `focus→wrapper` edges now point at folded nodes, so a surviving service may have no
edge from the focus. After the existing
`edges, resolved_order = _build_type_edges(diagram_type, component_name, callers, callees, children, override.get("order"), spec)`
line, append synthetic edges for any folded survivor not already connected from the focus:
```python
if folded_map:
    connected = {e.target for e in edges if e.source == component_name}
    edges += [
        TemplateEdge(source=component_name, target=s, edge_type="call")
        for s in folded_map if s not in connected
    ]
```
(`pipeline` and `hierarchy` already chain focus→steps, so this only adds edges for the `raw`/
`layered` cases — exactly the survivors that need them.)

### 2d — Expose folded info in meta
Where the method assembles `meta` (the dict with `focus`/`callers`/`callees`/`children`/`hub_id`/
`depth_map`, plus the conditional `order`/`rationale`), add:
```python
if folded_map:
    meta["folded"] = folded_map
```
Keep everything else (node building, `depth_map`, `order`, `rationale`) unchanged.

## Acceptance / verification (throwaway snippet, do NOT commit a test)
Load `shared/outputs/tracer_output.json`, rebuild the `DiagramSpec`, build a `_ViewBuilder`
(`from helpers.component_archetype_classifier import ComponentArchetypeClassifier`), compute the
`view_set` the way `ViewPlanner._view_set` does, then assert:
1. `build_component(spec, "TracerService", view_set)`: node ids **include**
   `CallGraphService`, `EvidenceService`, `FileFetchService` and **exclude** `BuildCallGraphTool`,
   `BuildEvidenceTool`, `FetchLayerFilesTool`; every one of the three services has an edge whose
   source is `TracerService`; `meta["folded"]` maps each service to its wrapper.
2. `build_component(spec, "CallGraphService", view_set)`: returns `type == "container"`, with
   `BuildCallGraphTool` as a member node parented to the container and `TracerService` present as a
   caller node.
3. `python3 -c "import ast; ast.parse(open(p).read())"` parses both touched files; `wc -l` shows both
   ≤150 lines.

Run from the layout agent's import root so `from services...`/`from helpers...`/`from shared...`
resolve (see how the agent is launched, e.g. its `main.py`/uvicorn cwd). Delete any temp file after.

## Out of scope
No `frontend/` changes. No changes to `_edge_builder.py`, `_graph_contraction.py`,
`_container_builder.py`, `_neighborhood.py`, or `view_planner.py` (other than leaving them working).
No new tests committed.
